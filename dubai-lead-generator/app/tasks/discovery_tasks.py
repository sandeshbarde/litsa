"""
Scheduled Discovery & Autonomous Rotation Task.
Picks next 15-20 unprocessed area x category combinations from rotation queue,
runs full discovery -> filter -> contact -> pitch -> send, and schedules follow-up in outreach_queue.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from loguru import logger

from app.config import yaml_config, settings
from app.database.db import SessionLocal
from app.services.discovery import DiscoveryService
from app.services.email_automation import EmailAutomationService
from app.models import OutreachQueue, Business
from app.tasks.celery_app import celery_app

ROTATION_STATE_FILE = "scratch/rotation_state.json"


def get_rotation_index() -> int:
    """Read last processed rotation queue index."""
    if os.path.exists(ROTATION_STATE_FILE):
        try:
            with open(ROTATION_STATE_FILE, "r") as f:
                data = json.load(f)
                return int(data.get("last_index", 0))
        except Exception:
            return 0
    return 0


def save_rotation_index(index: int) -> None:
    """Persist current rotation queue index."""
    os.makedirs(os.path.dirname(ROTATION_STATE_FILE), exist_ok=True)
    try:
        with open(ROTATION_STATE_FILE, "w") as f:
            json.dump({"last_index": index, "updated_at": datetime.utcnow().isoformat()}, f)
    except Exception as exc:
        logger.warning(f"Failed to save rotation state: {exc}")


@celery_app.task(bind=True, name="app.tasks.discovery_tasks.run_scheduled_rotation_task")
def run_scheduled_rotation_task(self, batch_size: int = 15) -> Dict[str, Any]:
    """
    Celery Beat task for automated rotation discovery & outreach.
    Executes next 15-20 area x category combinations, runs pipeline,
    and enqueues 3-day follow-ups in outreach_queue.
    """
    logger.info(f"[Scheduled Task] Starting automated rotation discovery (batch_size={batch_size})")
    db = SessionLocal()
    try:
        service = DiscoveryService(db)
        auto_svc = EmailAutomationService(db)

        # Generate all query combinations
        all_queries = service.generate_queries(
            areas=yaml_config.areas,
            categories=yaml_config.categories,
            city=yaml_config.default_city or "Dubai",
            country=yaml_config.default_country or "United Arab Emirates",
        )

        total_combos = len(all_queries)
        if total_combos == 0:
            return {"status": "skipped", "reason": "No query combinations generated."}

        current_idx = get_rotation_index()
        selected_queries = []
        for i in range(batch_size):
            idx = (current_idx + i) % total_combos
            selected_queries.append(all_queries[idx])

        new_next_idx = (current_idx + batch_size) % total_combos
        save_rotation_index(new_next_idx)

        run_id = f"auto-cron-{str(uuid.uuid4())[:8]}"
        logger.info(f"[Scheduled Task] Picked {len(selected_queries)} combinations starting at index {current_idx}/{total_combos} (Run ID: {run_id})")

        # Execute discovery for selected queries
        discovered_count = 0
        scheduled_outreach_count = 0

        for q_info in selected_queries:
            job = service._execute_query(
                job_id=str(uuid.uuid4()),
                q_info=q_info,
                max_businesses=settings.max_businesses_per_query,
            )
            discovered_count += job.get("new", 0)

        db.commit()

        # Fetch recently discovered leads from this run to trigger pitch & outreach queueing
        recent_leads = (
            db.query(Business)
            .filter(Business.contacted == False)
            .order_by(Business.first_seen.desc())
            .limit(batch_size * 5)
            .all()
        )

        follow_up_due = datetime.utcnow() + timedelta(days=3)

        for biz in recent_leads:
            # Determine channel & recipient
            channel = biz.contact_channel or "email"
            recipient = biz.decision_maker_email or biz.email or biz.phone

            if channel == "email" and (biz.email or biz.decision_maker_email):
                target_email = biz.decision_maker_email or biz.email
                res = auto_svc.send_single_email(
                    recipient_email=target_email,
                    subject=f"Quick question re: {biz.business_name}",
                    body_text=f"Hi {biz.decision_maker_name or 'Leadership team'},\n\nNoticed {biz.business_name} currently operates without an official custom website...",
                )
                if res.get("success"):
                    biz.contacted = True
                    biz.contact_date = datetime.utcnow()
                    biz.sequence_stage = "STEP1_SENT"
                    biz.next_action_due = follow_up_due

            # Enqueue follow-up into outreach_queue table
            q_entry = OutreachQueue(
                id=str(uuid.uuid4()),
                business_id=biz.id,
                channel=channel,
                recipient=recipient,
                status="PENDING",
                scheduled_at=datetime.utcnow(),
                follow_up_date=follow_up_due,
                sequence_step=1,
                notes=f"Scheduled automated 3-day follow-up for {biz.business_name} via {channel}.",
            )
            db.add(q_entry)
            scheduled_outreach_count += 1

        db.commit()
        summary = {
            "run_id": run_id,
            "queries_processed": len(selected_queries),
            "rotation_index": new_next_idx,
            "discovered_leads": discovered_count,
            "scheduled_outreach": scheduled_outreach_count,
            "follow_up_date": follow_up_due.isoformat(),
        }
        logger.info(f"[Scheduled Task] Rotation task completed: {summary}")
        return {"status": "success", "summary": summary}
    except Exception as exc:
        logger.error(f"[Scheduled Task] Rotation task failed: {exc}")
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()

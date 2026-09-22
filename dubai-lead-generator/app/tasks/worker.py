"""
Celery Worker Tasks for LITSA Lead Generator.
Background task execution for long-running discovery, batch outreach, and asynchronous email verification.
"""

from typing import Optional, List, Dict, Any
from loguru import logger

from app.tasks.celery_app import celery_app
from app.database.db import SessionLocal
from app.services.discovery import DiscoveryService
from app.services.email_automation import EmailAutomationService
from app.services.zerobounce_service import zerobounce_service
from app.database import repositories as repo


@celery_app.task(bind=True, name="app.tasks.worker.run_discovery_task")
def run_discovery_task(
    self,
    run_id: str,
    areas: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    city: str = "Dubai",
    country: str = "United Arab Emirates",
    max_businesses: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute asynchronous B2B discovery run."""
    logger.info(f"[Celery] Starting discovery task for run_id={run_id} ({city}, {country})")
    db = SessionLocal()
    try:
        service = DiscoveryService(db)
        result = service.start_run(
            run_id=run_id,
            areas=areas,
            categories=categories,
            city=city,
            country=country,
            max_businesses=max_businesses,
        )
        logger.info(f"[Celery] Discovery task completed: {result}")
        return {"status": "success", "result": result}
    except Exception as exc:
        logger.error(f"[Celery] Discovery task failed: {exc}")
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.worker.dispatch_outreach_task")
def dispatch_outreach_task(
    self,
    language: str = "en",
    max_leads: int = 50,
    throttle_seconds: float = 1.0,
) -> Dict[str, Any]:
    """Execute asynchronous batch email outreach dispatch."""
    logger.info(f"[Celery] Starting batch outreach task (max={max_leads}, lang={language})")
    db = SessionLocal()
    try:
        auto_svc = EmailAutomationService(db)
        summary = auto_svc.dispatch_all_uncontacted(
            language=language,
            max_leads=max_leads,
            throttle_seconds=throttle_seconds,
        )
        logger.info(f"[Celery] Outreach task complete: {summary}")
        return {"status": "success", "summary": summary}
    except Exception as exc:
        logger.error(f"[Celery] Outreach task failed: {exc}")
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.worker.verify_lead_email_task")
def verify_lead_email_task(self, lead_id: str) -> Dict[str, Any]:
    """Asynchronously verify email for a lead and update deliverability record."""
    logger.info(f"[Celery] Verifying email for lead {lead_id}")
    db = SessionLocal()
    try:
        business = repo.get_business(db, lead_id)
        if not business:
            return {"status": "not_found", "lead_id": lead_id}

        auto_svc = EmailAutomationService(db)
        target_email = auto_svc._get_target_email(business)
        validation = zerobounce_service.validate_email(target_email)

        business.email_verification_status = validation.get("status")
        business.email_confidence_score = float(validation.get("confidence", 0.0))
        db.commit()

        return {
            "status": "success",
            "lead_id": lead_id,
            "email": target_email,
            "validation": validation,
        }
    except Exception as exc:
        logger.error(f"[Celery] Verification task failed: {exc}")
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()

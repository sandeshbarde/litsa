"""
Webhooks and Compliance API endpoints for LITSA Lead Generator.
Handles incoming delivery events (Resend webhooks), bounces, complaints,
and recipient unsubscribe requests with idempotent event processing.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from loguru import logger

from app.database.db import get_db
from app.database.repositories import (
    record_webhook_event,
    update_email_log_by_message_id,
    add_suppression,
    get_business,
)
from app.models import Business, EmailLog

router = APIRouter(prefix="/api/v1", tags=["Webhooks & Compliance"])


@router.post("/webhooks/resend")
async def resend_webhook_handler(request: Request, db: Session = Depends(get_db)):
    """
    Handle incoming Resend email delivery, bounce, and complaint webhooks.
    Idempotent: uses event_id to prevent double-processing.
    """
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Malformed JSON payload: {exc}")

    event_id = body.get("id") or body.get("created_at") or str(datetime.utcnow().timestamp())
    event_type = body.get("type", "").lower()
    data = body.get("data", {})
    email_id = data.get("email_id")
    recipient = (data.get("to") or [""])[0] if isinstance(data.get("to"), list) else data.get("to", "")

    # Idempotent tracking
    event, is_new = record_webhook_event(
        db=db,
        event_id=event_id,
        provider="resend",
        event_type=event_type,
        payload=body,
    )

    if not is_new:
        logger.info(f"Webhook event '{event_id}' already processed. Skipping duplicate.")
        return {"status": "skipped", "message": "Duplicate event ignored"}

    logger.info(f"Processing Resend webhook event '{event_type}' for message '{email_id}' ({recipient})")

    updates = {}
    if event_type == "email.delivered":
        updates["status"] = "DELIVERED"
        updates["delivered_at"] = datetime.utcnow()
    elif event_type == "email.bounced":
        updates["status"] = "BOUNCED"
        updates["bounced_at"] = datetime.utcnow()
        if recipient:
            add_suppression(db, email=recipient, reason="BOUNCED", source="resend_webhook")
    elif event_type == "email.complained":
        updates["status"] = "COMPLAINT"
        if recipient:
            add_suppression(db, email=recipient, reason="COMPLAINT", source="resend_webhook")
    elif event_type == "email.opened":
        updates["opened_at"] = datetime.utcnow()
    elif event_type == "email.clicked":
        updates["clicked_at"] = datetime.utcnow()
    elif event_type in ["email.replied", "email.received", "inbound.email", "email.inbound"]:
        updates["status"] = "REPLIED"
        if recipient:
            biz = db.query(Business).filter(
                (Business.email.ilike(recipient)) | (Business.decision_maker_email.ilike(recipient))
            ).first()
            if biz:
                biz.crm_status = "REPLIED"
                biz.contact_status = "replied"
                biz.sequence_stage = "REPLIED_PAUSED"
                biz.next_action_due = None
                db.commit()
                logger.info(f"Inbound reply event received for '{biz.business_name}' ({recipient}). Sequence PAUSED.")

    if email_id and updates:
        log = update_email_log_by_message_id(db, email_id, updates)
        if log and log.business_id:
            biz = get_business(db, log.business_id)
            if biz:
                if updates.get("status") == "BOUNCED":
                    biz.crm_status = "BOUNCED"
                    biz.contact_status = "bounced"
                elif updates.get("status") == "DELIVERED":
                    biz.crm_status = "DELIVERED"
                    biz.contact_status = "delivered"
                elif updates.get("status") == "REPLIED":
                    biz.crm_status = "REPLIED"
                    biz.contact_status = "replied"
                    biz.sequence_stage = "REPLIED_PAUSED"
                    biz.next_action_due = None
                db.commit()

    event.processed = True
    db.commit()

    return {"status": "processed", "event_id": event_id, "type": event_type}


@router.post("/webhooks/inbound-reply")
def inbound_reply_handler(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Handle inbound email reply webhook / notification.
    Immediately pauses automated drip follow-up sequence for the matching business.
    """
    from_email = payload.get("from_email") or payload.get("sender") or payload.get("from")
    if not from_email or "@" not in str(from_email):
        raise HTTPException(status_code=400, detail="Valid sender email required.")

    clean_email = str(from_email).strip().lower()
    biz = db.query(Business).filter(
        (Business.email.ilike(clean_email)) | (Business.decision_maker_email.ilike(clean_email))
    ).first()

    if not biz:
        return {"status": "not_found", "message": f"No business matching email '{clean_email}'"}

    biz.crm_status = "REPLIED"
    biz.contact_status = "replied"
    biz.sequence_stage = "REPLIED_PAUSED"
    biz.next_action_due = None
    db.commit()

    logger.info(f"Inbound reply recorded for '{biz.business_name}' ({clean_email}). Drip sequence PAUSED.")
    return {"status": "paused", "business_id": biz.id, "business_name": biz.business_name}


@router.get("/outreach/unsubscribe")
def unsubscribe_recipient_get(email: str, db: Session = Depends(get_db)):
    """Handles 1-Click unsubscribe links embedded in emails."""
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address specified.")

    clean_email = email.strip().lower()
    add_suppression(db, email=clean_email, reason="UNSUBSCRIBED", source="unsubscribe_link")

    # Update any business matching this email
    biz = db.query(Business).filter(
        (Business.email.ilike(clean_email)) | (Business.decision_maker_email.ilike(clean_email))
    ).first()
    if biz:
        biz.crm_status = "UNSUBSCRIBED"
        biz.contact_status = "unsubscribed"
        db.commit()

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unsubscribed Successfully</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
            .card {{ background: #1e293b; padding: 2.5rem; border-radius: 12px; border: 1px solid #334155; text-align: center; max-width: 480px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            h2 {{ color: #38bdf8; margin-bottom: 0.5rem; }}
            p {{ color: #94a3b8; line-height: 1.5; }}
            .badge {{ display: inline-block; background: #059669; color: white; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; margin-top: 1rem; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>You Have Been Unsubscribed</h2>
            <p><strong>{clean_email}</strong> has been permanently added to our suppression list. You will not receive further automated communications from us.</p>
            <div class="badge">Status: Suppressed</div>
        </div>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")


@router.post("/outreach/suppress")
def manual_suppress_email(
    payload: Dict[str, str],
    db: Session = Depends(get_db),
):
    """Admin endpoint to manually add an email to the suppression table."""
    email = payload.get("email", "").strip()
    reason = payload.get("reason", "MANUAL").strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email is required.")

    supp = add_suppression(db, email=email, reason=reason, source="admin_manual")
    return {"status": "success", "suppressed": supp.to_dict()}

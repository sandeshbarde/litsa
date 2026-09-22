"""
Repository layer: all DB CRUD operations.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models import (
    Business,
    SearchJob,
    VerificationResult,
    ApiUsage,
    OutreachDraft,
    Suppression,
    EmailLog,
    WebhookEvent,
    DemoInteraction,
)


# ─────────────────────────────────────────────
# Business Repository
# ─────────────────────────────────────────────

def get_business(db: Session, business_id: str) -> Optional[Business]:
    return db.query(Business).filter(Business.id == business_id).first()


def get_business_by_place_id(db: Session, place_id: str) -> Optional[Business]:
    return db.query(Business).filter(Business.place_id == place_id).first()


def get_business_by_data_id(db: Session, data_id: str) -> Optional[Business]:
    return db.query(Business).filter(Business.data_id == data_id).first()


def get_businesses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None,
    area: Optional[str] = None,
    category: Optional[str] = None,
    business_type: Optional[str] = None,
    is_dealer_or_wholesale: Optional[bool] = None,
    lead_priority: Optional[str] = None,
    website_status: Optional[str] = None,
    contact_status: Optional[str] = None,
    contacted: Optional[bool] = None,
    min_score: Optional[int] = None,
) -> List[Business]:
    q = db.query(Business)
    if city and city.strip():
        q = q.filter(Business.city.ilike(f"%{city.strip()}%"))
    if area and area.strip():
        q = q.filter(Business.area.ilike(f"%{area.strip()}%"))
    if category and category.strip():
        q = q.filter(Business.category.ilike(f"%{category.strip()}%"))
    if business_type and business_type.strip():
        q = q.filter(Business.business_type == business_type.strip().upper())
    if is_dealer_or_wholesale is not None:
        q = q.filter(Business.is_dealer_or_wholesale == is_dealer_or_wholesale)
    if lead_priority:
        q = q.filter(Business.lead_priority == lead_priority)
    if website_status:
        q = q.filter(Business.website_status == website_status)
    if contact_status:
        q = q.filter(Business.contact_status == contact_status)
    if contacted is not None:
        q = q.filter(Business.contacted == contacted)
    if min_score is not None:
        q = q.filter(Business.lead_score >= min_score)
    return q.order_by(Business.lead_score.desc()).offset(skip).limit(limit).all()


def count_businesses(
    db: Session,
    city: Optional[str] = None,
    area: Optional[str] = None,
    category: Optional[str] = None,
    business_type: Optional[str] = None,
    is_dealer_or_wholesale: Optional[bool] = None,
    lead_priority: Optional[str] = None,
    website_status: Optional[str] = None,
    contacted: Optional[bool] = None,
    min_score: Optional[int] = None,
    crm_status: Optional[str] = None,
    **kwargs,
) -> int:
    q = db.query(func.count(Business.id))
    if city and city.strip():
        q = q.filter(Business.city.ilike(f"%{city.strip()}%"))
    if area and area.strip():
        q = q.filter(Business.area.ilike(f"%{area.strip()}%"))
    if category and category.strip():
        q = q.filter(Business.category.ilike(f"%{category.strip()}%"))
    if business_type and business_type.strip():
        q = q.filter(Business.business_type == business_type.strip().upper())
    if is_dealer_or_wholesale is not None:
        q = q.filter(Business.is_dealer_or_wholesale == is_dealer_or_wholesale)
    if lead_priority:
        q = q.filter(Business.lead_priority == lead_priority)
    if website_status:
        q = q.filter(Business.website_status == website_status)
    if contacted is not None:
        q = q.filter(Business.contacted == contacted)
    if min_score is not None:
        q = q.filter(Business.lead_score >= min_score)
    if crm_status:
        q = q.filter(Business.crm_status == crm_status)
    return q.scalar() or 0


def create_business(db: Session, data: dict) -> Business:
    business = Business(**data)
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


def update_business(db: Session, business_id: str, updates: dict) -> Optional[Business]:
    business = get_business(db, business_id)
    if not business:
        return None
    for key, value in updates.items():
        setattr(business, key, value)
    business.last_checked = datetime.utcnow()
    db.commit()
    db.refresh(business)
    return business


def get_businesses_needing_verification(db: Session, limit: int = 50) -> List[Business]:
    """Get businesses that haven't been verified or need re-verification."""
    return (
        db.query(Business)
        .filter(
            or_(
                Business.website_status.is_(None),
                Business.website_status == "",
            )
        )
        .limit(limit)
        .all()
    )


def get_businesses_for_sheet_sync(db: Session, limit: int = 500) -> List[Business]:
    """Get all businesses ordered by lead score for sheet sync."""
    return db.query(Business).order_by(Business.lead_score.desc()).limit(limit).all()


def get_all_phone_normalized(db: Session) -> List[str]:
    rows = db.query(Business.phone_normalized).filter(Business.phone_normalized.isnot(None)).all()
    return [r[0] for r in rows if r[0]]


def get_all_name_area_pairs(db: Session) -> List[tuple]:
    rows = db.query(Business.business_name_normalized, Business.area).all()
    return [(r[0], r[1]) for r in rows if r[0]]


# ─────────────────────────────────────────────
# SearchJob Repository
# ─────────────────────────────────────────────

def create_job(db: Session, data: dict) -> SearchJob:
    job = SearchJob(**data)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> Optional[SearchJob]:
    return db.query(SearchJob).filter(SearchJob.id == job_id).first()


def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    parent_run_id: Optional[str] = None,
) -> List[SearchJob]:
    q = db.query(SearchJob)
    if status:
        q = q.filter(SearchJob.status == status)
    if parent_run_id:
        q = q.filter(SearchJob.parent_run_id == parent_run_id)
    return q.order_by(SearchJob.started_at.desc()).offset(skip).limit(limit).all()


def update_job(db: Session, job_id: str, updates: dict) -> Optional[SearchJob]:
    job = get_job(db, job_id)
    if not job:
        return None
    for key, value in updates.items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


# ─────────────────────────────────────────────
# VerificationResult Repository
# ─────────────────────────────────────────────

def create_verification(db: Session, data: dict) -> VerificationResult:
    v = VerificationResult(**data)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


# ─────────────────────────────────────────────
# ApiUsage Repository
# ─────────────────────────────────────────────

def record_api_call(
    db: Session, engine: str, error: bool = False
) -> None:
    today = date.today().isoformat()
    usage = (
        db.query(ApiUsage)
        .filter(ApiUsage.date == today, ApiUsage.engine == engine)
        .first()
    )
    if not usage:
        usage = ApiUsage(date=today, engine=engine, call_count=0, error_count=0)
        db.add(usage)
    usage.call_count += 1
    if error:
        usage.error_count += 1
    usage.last_called_at = datetime.utcnow()
    db.commit()


def get_api_usage_today(db: Session) -> List[Dict[str, Any]]:
    today = date.today().isoformat()
    rows = db.query(ApiUsage).filter(ApiUsage.date == today).all()
    return [
        {
            "engine": r.engine,
            "call_count": r.call_count,
            "error_count": r.error_count,
            "last_called_at": r.last_called_at.isoformat() if r.last_called_at else None,
        }
        for r in rows
    ]


# ─────────────────────────────────────────────
# OutreachDraft Repository
# ─────────────────────────────────────────────

def create_outreach_draft(db: Session, data: dict) -> OutreachDraft:
    draft = OutreachDraft(**data)
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def get_outreach_drafts_for_business(
    db: Session, business_id: str
) -> List[OutreachDraft]:
    return (
        db.query(OutreachDraft)
        .filter(OutreachDraft.business_id == business_id)
        .order_by(OutreachDraft.created_at.desc())
        .all()
    )


# ─────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────

def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    total = db.query(func.count(Business.id)).scalar() or 0
    no_website = (
        db.query(func.count(Business.id))
        .filter(Business.website_status == "NO_WEBSITE")
        .scalar() or 0
    )
    website_found = (
        db.query(func.count(Business.id))
        .filter(Business.website_status.in_(["WEBSITE_FOUND", "WEBSITE_WORKING"]))
        .scalar() or 0
    )
    website_broken = (
        db.query(func.count(Business.id))
        .filter(Business.website_status == "WEBSITE_BROKEN")
        .scalar() or 0
    )
    hot = (
        db.query(func.count(Business.id))
        .filter(Business.lead_priority == "HOT")
        .scalar() or 0
    )
    warm = (
        db.query(func.count(Business.id))
        .filter(Business.lead_priority == "WARM")
        .scalar() or 0
    )
    low = (
        db.query(func.count(Business.id))
        .filter(Business.lead_priority == "LOW")
        .scalar() or 0
    )
    jobs_total = db.query(func.count(SearchJob.id)).scalar() or 0
    jobs_completed = (
        db.query(func.count(SearchJob.id))
        .filter(SearchJob.status == "completed")
        .scalar() or 0
    )
    today_api = get_api_usage_today(db)
    total_calls = sum(r["call_count"] for r in today_api)
    total_errors = sum(r["error_count"] for r in today_api)

    # Email Outreach Analytics
    sent_count = db.query(func.count(EmailLog.id)).filter(EmailLog.status.in_(["SENT", "ACCEPTED", "DELIVERED"])).scalar() or 0
    open_count = db.query(func.count(EmailLog.id)).filter(EmailLog.opened_at.isnot(None)).scalar() or 0
    bounce_count = db.query(func.count(EmailLog.id)).filter(EmailLog.status == "BOUNCED").scalar() or 0
    reply_count = db.query(func.count(Business.id)).filter(Business.contact_status == "replied").scalar() or 0
    demo_view_count = db.query(func.count(DemoInteraction.id)).scalar() or 0
    manual_research_needed = db.query(func.count(Business.id)).filter(Business.contact_status == "manual_research_needed").scalar() or 0

    open_rate = round((open_count / sent_count * 100), 1) if sent_count > 0 else 0.0
    reply_rate = round((reply_count / sent_count * 100), 1) if sent_count > 0 else 0.0
    demo_view_rate = round((demo_view_count / sent_count * 100), 1) if sent_count > 0 else 0.0
    bounce_rate = round((bounce_count / sent_count * 100), 1) if sent_count > 0 else 0.0

    return {
        "total_businesses": total,
        "no_website": no_website,
        "website_found": website_found,
        "website_broken": website_broken,
        "hot_leads": hot,
        "warm_leads": warm,
        "low_leads": low,
        "jobs_total": jobs_total,
        "jobs_completed": jobs_completed,
        "api_calls_today": total_calls,
        "api_errors_today": total_errors,
        "api_usage_breakdown": today_api,
        "email_analytics": {
            "sent_count": sent_count,
            "open_count": open_count,
            "open_rate": open_rate,
            "reply_count": reply_count,
            "reply_rate": reply_rate,
            "demo_view_count": demo_view_count,
            "demo_view_rate": demo_view_rate,
            "bounce_count": bounce_count,
            "bounce_rate": bounce_rate,
            "manual_research_needed": manual_research_needed,
        },
    }


# ─────────────────────────────────────────────
# Suppression & Compliance Repository
# ─────────────────────────────────────────────

def is_email_suppressed(db: Session, email: str) -> bool:
    """Check if an email is suppressed (unsubscribed, bounced, complaint)."""
    if not email:
        return False
    normalized = email.strip().lower()
    return db.query(Suppression).filter(func.lower(Suppression.email) == normalized).first() is not None


def add_suppression(
    db: Session, email: str, reason: str, source: Optional[str] = None
) -> Suppression:
    """Add an email to the suppression table."""
    normalized = email.strip().lower()
    existing = db.query(Suppression).filter(func.lower(Suppression.email) == normalized).first()
    if existing:
        return existing
    supp = Suppression(email=normalized, reason=reason.upper(), source=source)
    db.add(supp)
    db.commit()
    db.refresh(supp)
    return supp


# ─────────────────────────────────────────────
# Email Log & Webhooks Repository
# ─────────────────────────────────────────────

def create_email_log(db: Session, log_data: dict) -> EmailLog:
    """Create an email audit log record."""
    email_log = EmailLog(**log_data)
    db.add(email_log)
    db.commit()
    db.refresh(email_log)
    return email_log


def update_email_log_by_message_id(
    db: Session, provider_message_id: str, updates: dict
) -> Optional[EmailLog]:
    """Update email log status by provider message ID (e.g. from webhook)."""
    log = db.query(EmailLog).filter(EmailLog.provider_message_id == provider_message_id).first()
    if not log:
        return None
    for k, v in updates.items():
        setattr(log, k, v)
    db.commit()
    db.refresh(log)
    return log


def record_webhook_event(
    db: Session, event_id: str, provider: str, event_type: str, payload: dict
) -> Tuple[WebhookEvent, bool]:
    """Record an incoming webhook event. Returns (event, is_new)."""
    existing = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first()
    if existing:
        return existing, False

    event = WebhookEvent(
        event_id=event_id,
        provider=provider,
        event_type=event_type,
        payload=payload,
        processed=False,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event, True


# ─────────────────────────────────────────────
# Demo Interactions Repository
# ─────────────────────────────────────────────

def record_demo_interaction(
    db: Session,
    business_id: str,
    interaction_type: str,
    visitor_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    meta_data: Optional[dict] = None,
) -> DemoInteraction:
    """Record a visitor interaction with a generated demo website."""
    interaction = DemoInteraction(
        business_id=business_id,
        interaction_type=interaction_type,
        visitor_ip=visitor_ip,
        user_agent=user_agent,
        meta_data=meta_data or {},
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


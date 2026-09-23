"""
SQLAlchemy ORM models for the Dubai Business Lead Generator.
"""

import uuid
import json
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Business(Base):
    """Core business/lead record."""

    __tablename__ = "businesses"

    id = Column(String, primary_key=True, default=generate_uuid)
    place_id = Column(String, nullable=True, index=True)
    data_id = Column(String, nullable=True, index=True)

    # Identity
    business_name = Column(String, nullable=False)
    business_name_normalized = Column(String, nullable=True)
    category = Column(String, nullable=True)
    area = Column(String, nullable=True)
    address = Column(String, nullable=True)
    address_normalized = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    phone_normalized = Column(String, nullable=True)
    email = Column(String, nullable=True)

    # Web presence
    website = Column(String, nullable=True)
    website_status = Column(String, nullable=True)  # NO_WEBSITE, WEBSITE_FOUND, etc.
    website_url_verified = Column(String, nullable=True)
    website_quality = Column(String, nullable=True)  # good, basic, missing, broken

    # Maps data
    google_maps_url = Column(String, nullable=True)
    google_rating = Column(Float, nullable=True)
    google_review_count = Column(Integer, nullable=True)

    # Social
    instagram_url = Column(String, nullable=True)
    facebook_url = Column(String, nullable=True)
    other_social_url = Column(String, nullable=True)

    # Business info
    business_status = Column(String, nullable=True)  # OPERATIONAL, CLOSED_TEMPORARILY
    open_state = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    booking_link = Column(String, nullable=True)
    has_booking = Column(Boolean, default=False)

    # Lead scoring
    lead_score = Column(Integer, default=0)
    lead_priority = Column(String, nullable=True)  # HOT, WARM, LOW
    score_breakdown = Column(JSON, nullable=True)
    score_version = Column(String, default="v2.0")
    score_reasons = Column(JSON, nullable=True)

    # CRM Lifecycle
    crm_status = Column(String, default="DISCOVERED")  # DISCOVERED, ENRICHED, EMAIL_FOUND, VERIFIED, PITCH_READY, DEMO_READY, SENT, DELIVERED, REPLIED, MEETING, WON, LOST, BOUNCED, UNSUBSCRIBED, SUPPRESSED

    # Meta
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    source = Column(String, nullable=True)  # serpapi_maps, manual

    # Global location
    city = Column(String, default="Dubai")
    state = Column(String, nullable=True)
    country = Column(String, default="United Arab Emirates")

    # Business classification
    business_type = Column(String, default="B2B")  # B2B or B2C
    is_dealer_or_wholesale = Column(Boolean, default=False)

    # Decision Maker (CEO / Owner / Founder / MD)
    decision_maker_name = Column(String, nullable=True)
    decision_maker_title = Column(String, nullable=True)  # CEO, Managing Director, Founder, Owner
    decision_maker_email = Column(String, nullable=True)
    decision_maker_linkedin = Column(String, nullable=True)

    # Loophole Research & Company Profiling
    loophole_summary = Column(Text, nullable=True)
    loophole_data = Column(JSON, nullable=True)

    # Outreach & Automated Sequence
    contacted = Column(Boolean, default=False)
    contact_date = Column(DateTime, nullable=True)
    contact_status = Column(String, nullable=True)
    sequence_stage = Column(String, default="NOT_STARTED")  # NOT_STARTED, STEP1_SENT, STEP2_SENT, STEP3_SENT, REPLIED
    next_action_due = Column(DateTime, nullable=True)
    response = Column(Text, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    verifications = relationship(
        "VerificationResult", back_populates="business", cascade="all, delete-orphan"
    )
    outreach_drafts = relationship(
        "OutreachDraft", back_populates="business", cascade="all, delete-orphan"
    )
    email_logs = relationship(
        "EmailLog", back_populates="business", cascade="all, delete-orphan"
    )
    demo_interactions = relationship(
        "DemoInteraction", back_populates="business", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_business_name_area", "business_name_normalized", "area"),
        Index("ix_phone_normalized", "phone_normalized"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "place_id": self.place_id,
            "data_id": self.data_id,
            "business_name": self.business_name,
            "category": self.category,
            "city": self.city or "Dubai",
            "state": self.state or "",
            "country": self.country or "United Arab Emirates",
            "business_type": self.business_type or "B2B",
            "is_dealer_or_wholesale": self.is_dealer_or_wholesale or False,
            "area": self.area,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "decision_maker_name": self.decision_maker_name,
            "decision_maker_title": self.decision_maker_title,
            "decision_maker_email": self.decision_maker_email,
            "decision_maker_linkedin": self.decision_maker_linkedin,
            "loophole_summary": self.loophole_summary,
            "loophole_data": self.loophole_data,
            "website": self.website,
            "website_status": self.website_status,
            "website_url_verified": self.website_url_verified,
            "website_quality": self.website_quality,
            "google_maps_url": self.google_maps_url,
            "google_rating": self.google_rating,
            "google_review_count": self.google_review_count,
            "instagram_url": self.instagram_url,
            "facebook_url": self.facebook_url,
            "other_social_url": self.other_social_url,
            "business_status": self.business_status,
            "open_state": self.open_state,
            "description": self.description,
            "booking_link": self.booking_link,
            "has_booking": self.has_booking,
            "lead_score": self.lead_score,
            "lead_priority": self.lead_priority,
            "score_breakdown": self.score_breakdown,
            "score_version": self.score_version or "v2.0",
            "score_reasons": self.score_reasons or {},
            "crm_status": self.crm_status or "DISCOVERED",
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "source": self.source,
            "contacted": self.contacted,
            "contact_date": self.contact_date.isoformat() if self.contact_date else None,
            "contact_status": self.contact_status,
            "sequence_stage": self.sequence_stage or "NOT_STARTED",
            "next_action_due": self.next_action_due.isoformat() if self.next_action_due else None,
            "response": self.response,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "notes": self.notes,
        }


class SearchJob(Base):
    """Tracks each area × category search job."""

    __tablename__ = "search_jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    area = Column(String, nullable=False)
    category = Column(String, nullable=False)
    query = Column(String, nullable=False)
    status = Column(
        String, default="pending"
    )  # pending, running, paused, completed, cancelled, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    results_found = Column(Integer, default=0)
    errors = Column(Text, nullable=True)
    parent_run_id = Column(String, nullable=True, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "area": self.area,
            "category": self.category,
            "query": self.query,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results_found": self.results_found,
            "errors": self.errors,
            "parent_run_id": self.parent_run_id,
        }


class VerificationResult(Base):
    """Stores website/social verification results per business."""

    __tablename__ = "verification_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    checked_at = Column(DateTime, default=datetime.utcnow)
    url_checked = Column(String, nullable=True)
    http_status_code = Column(Integer, nullable=True)
    resolved = Column(Boolean, nullable=True)
    redirect_url = Column(String, nullable=True)
    website_status = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    business = relationship("Business", back_populates="verifications")


class ApiUsage(Base):
    """Tracks API call counts per engine per day."""

    __tablename__ = "api_usage"

    id = Column(String, primary_key=True, default=generate_uuid)
    date = Column(String, nullable=False, index=True)  # YYYY-MM-DD
    engine = Column(String, nullable=False)  # serpapi_maps, serpapi_google, gemini, etc.
    call_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_called_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("ix_api_usage_date_engine", "date", "engine", unique=True),)


class OutreachDraft(Base):
    """Generated outreach drafts per business."""

    __tablename__ = "outreach_drafts"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    pitch_text = Column(Text, nullable=True)
    pitch_angle = Column(String, nullable=True)
    website_quality = Column(String, nullable=True)
    business_relevance = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    model_used = Column(String, nullable=True)

    business = relationship("Business", back_populates="outreach_drafts")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "business_id": self.business_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "pitch_text": self.pitch_text,
            "pitch_angle": self.pitch_angle,
            "website_quality": self.website_quality,
            "business_relevance": self.business_relevance,
            "reason": self.reason,
            "model_used": self.model_used,
        }


class Suppression(Base):
    """Email suppression table to block outreach to unsubscribed, bounced, or complaint recipients."""

    __tablename__ = "suppressions"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, nullable=False, unique=True, index=True)
    reason = Column(String, nullable=False)  # UNSUBSCRIBED, BOUNCED, COMPLAINT, MANUAL
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "reason": self.reason,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EmailLog(Base):
    """Durable audit trail for every outreach email attempt and webhook event."""

    __tablename__ = "email_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    recipient_email = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False)
    provider = Column(String, nullable=False)  # resend, smtp, simulation
    provider_message_id = Column(String, nullable=True, index=True)
    status = Column(
        String, default="DRAFT"
    )  # DRAFT, QUEUED, SEND_ATTEMPTED, ACCEPTED, DELIVERED, BOUNCED, COMPLAINT, FAILED, UNSUBSCRIBED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    bounced_at = Column(DateTime, nullable=True)

    business = relationship("Business", back_populates="email_logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "business_id": self.business_id,
            "recipient_email": self.recipient_email,
            "subject": self.subject,
            "provider": self.provider,
            "provider_message_id": self.provider_message_id,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "bounced_at": self.bounced_at.isoformat() if self.bounced_at else None,
        }


class WebhookEvent(Base):
    """Stores incoming webhook events for idempotent processing."""

    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_id = Column(String, nullable=False, unique=True, index=True)
    provider = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DemoInteraction(Base):
    """Tracks visitor interactions with generated demo websites."""

    __tablename__ = "demo_interactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    interaction_type = Column(
        String, nullable=False
    )  # demo_view, cta_click, phone_click, whatsapp_click, form_submit
    visitor_ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="demo_interactions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "business_id": self.business_id,
            "interaction_type": self.interaction_type,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


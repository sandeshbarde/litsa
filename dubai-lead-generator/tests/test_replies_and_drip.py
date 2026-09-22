"""
Tests for Priority 3: Reply Detection, Sequence Pausing, and High-Intent Demo Visitor Escalation.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.database.db import SessionLocal
from app.models import Business, DemoInteraction
from app.services.email_automation import EmailAutomationService


client = TestClient(app)


def test_inbound_reply_pauses_sequence():
    """Verify inbound reply webhook marks business as REPLIED and pauses sequence."""
    db = SessionLocal()
    biz = None
    try:
        biz = Business(
            id="biz_reply_test_1",
            business_name="Dubai Auto Parts",
            email="owner@dubaiauto.ae",
            decision_maker_email="owner@dubaiauto.ae",
            contacted=True,
            crm_status="SENT",
            contact_status="auto_sent_resend",
            sequence_stage="STEP1_SENT",
        )
        biz = db.merge(biz)
        db.commit()

        resp = client.post(
            "/api/v1/webhooks/inbound-reply",
            json={"from_email": "owner@dubaiauto.ae", "subject": "Re: Custom Website Proposal"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "paused"

        db.refresh(biz)
        assert biz.crm_status == "REPLIED"
        assert biz.contact_status == "replied"
        assert biz.sequence_stage == "REPLIED_PAUSED"
        assert biz.next_action_due is None
    finally:
        if biz:
            db.delete(biz)
            db.commit()
        db.close()


def test_demo_2x_visit_escalates_to_hot():
    """Verify visiting demo 2x+ escalates lead priority to HOT and sets HIGH_INTENT_DEMO_VISITOR."""
    db = SessionLocal()
    biz = None
    try:
        biz = Business(
            id="biz_demo_test_2",
            business_name="Al Rigga Barber",
            lead_score=50,
            lead_priority="LOW",
            crm_status="NOT_STARTED",
        )
        biz = db.merge(biz)
        db.commit()

        # First visit
        resp1 = client.post(f"/leads/{biz.id}/demo-interaction", json={"interaction_type": "pageview"})
        assert resp1.status_code == 200
        assert resp1.json()["visit_count"] == 1
        assert resp1.json()["is_high_intent"] is False

        # Second visit
        resp2 = client.post(f"/leads/{biz.id}/demo-interaction", json={"interaction_type": "pageview"})
        assert resp2.status_code == 200
        assert resp2.json()["visit_count"] == 2
        assert resp2.json()["is_high_intent"] is True

        db.refresh(biz)
        assert biz.lead_priority == "HOT"
        assert biz.lead_score == 70
        assert biz.crm_status == "HIGH_INTENT_DEMO_VISITOR"
    finally:
        if biz:
            db.delete(biz)
            db.commit()
        db.close()

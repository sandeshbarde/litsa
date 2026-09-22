"""
Tests for email webhook handling, suppression lists, and 1-click unsubscribe.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.db import SessionLocal
from app.database import repositories as repo


@pytest.fixture
def client():
    return TestClient(app)


def test_suppression_repository():
    db = SessionLocal()
    try:
        test_email = f"bounced_{uuid.uuid4().hex[:8]}@test-domain.com"
        # Initially not suppressed
        assert repo.is_email_suppressed(db, test_email) is False

        # Add suppression
        rec = repo.add_suppression(
            db=db,
            email=test_email,
            reason="hard_bounce",
            source="test_suite",
        )
        assert rec is not None
        assert rec.email == test_email

        # Now suppressed
        assert repo.is_email_suppressed(db, test_email) is True
    finally:
        db.close()


def test_unsubscribe_endpoint(client):
    unique_email = f"optout_{uuid.uuid4().hex[:8]}@customer.com"
    res = client.get(f"/api/v1/outreach/unsubscribe?email={unique_email}")
    assert res.status_code == 200
    assert "Unsubscribed" in res.text or "unsubscribed" in res.text.lower()

    # Verify email is now in suppression table
    db = SessionLocal()
    try:
        assert repo.is_email_suppressed(db, unique_email) is True
    finally:
        db.close()


def test_resend_webhook_delivered(client):
    event_id = f"evt_test_resend_{uuid.uuid4().hex[:10]}"
    payload = {
        "id": event_id,
        "type": "email.delivered",
        "data": {
            "email_id": f"msg_test_{uuid.uuid4().hex[:8]}",
            "to": ["client@retailer.com"],
        }
    }
    res = client.post("/api/v1/webhooks/resend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "processed"

    # Test idempotency (duplicate webhook event)
    res_dup = client.post("/api/v1/webhooks/resend", json=payload)
    assert res_dup.status_code == 200
    assert res_dup.json()["status"] in ["already_processed", "skipped"]

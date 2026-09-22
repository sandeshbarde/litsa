"""
Tests for live demo interactions and customer form submissions.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.db import SessionLocal
from app.models import Business
from app.config import build_demo_url


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_lead():
    db = SessionLocal()
    biz = Business(
        id="lead_demo_test_001",
        business_name="Falcon Trading LLC",
        category="General Trading",
        city="Dubai",
        website_status="NO_WEBSITE",
    )
    db.merge(biz)
    db.commit()
    db.close()
    return "lead_demo_test_001"


def test_build_demo_url():
    lead_id = "abc_123"
    url = build_demo_url(lead_id)
    assert url.endswith(f"/demo/{lead_id}")


def test_track_demo_interaction(client, test_lead):
    payload = {
        "interaction_type": "scroll_75",
        "meta_data": {"scroll_depth": 75, "time_on_page": 24},
    }
    res = client.post(f"/leads/{test_lead}/demo-interaction", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["interaction_type"] == "scroll_75"
    assert data["lead_id"] == test_lead


def test_submit_demo_inquiry(client, test_lead):
    payload = {
        "client_name": "Tariq Mansoor",
        "client_email": "tariq@falcontrading.ae",
        "client_phone": "+971 50 999 8888",
        "service_requested": "Custom Quotation System",
        "message": "We saw the preview and want to deploy this portal.",
    }
    res = client.post(f"/leads/{test_lead}/demo-form-submit", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "Inquiry successfully recorded" in data["message"]

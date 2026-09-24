"""
Tests for lead listing, filtering, and priority query aliases.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_leads_returns_dict(client):
    res = client.get("/leads")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "leads" in data
    assert isinstance(data["leads"], list)


def test_list_leads_filter_priority(client):
    res_lead_priority = client.get("/leads?lead_priority=HOT")
    res_priority = client.get("/leads?priority=HOT")
    assert res_lead_priority.status_code == 200
    assert res_priority.status_code == 200
    assert res_lead_priority.json()["total"] == res_priority.json()["total"]


def test_list_jobs_format(client):
    res = client.get("/jobs")
    assert res.status_code == 200
    data = res.json()
    assert "jobs" in data
    assert isinstance(data["jobs"], list)


def test_automation_status(client):
    res = client.get("/leads/automation/status")
    assert res.status_code == 200
    data = res.json()
    assert "connection" in data
    assert "total_targets_no_website" in data
    assert "contacted_count" in data
    assert "uncontacted_pending" in data


def test_automation_test_connection(client):
    res = client.post("/leads/automation/test-connection")
    assert res.status_code == 200
    data = res.json()
    assert "active" in data
    assert "provider" in data


def test_automation_dispatch_staged(client):
    # Tests that dispatch-all executes cleanly without error
    res = client.post("/leads/automation/dispatch-all", json={"language": "en", "max_leads": 2, "throttle_seconds": 0.0})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "summary" in data
    assert "dispatched" in data["summary"]


def test_whatsapp_broadcast_endpoint(client):
    res = client.post("/leads/whatsapp-broadcast", json={"business_type": "ALL", "language": "en", "mark_as_contacted": False})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "total_targets" in data
    assert "total_with_phone" in data
    assert "broadcast_list" in data


def test_export_whatsapp_csv(client):
    res = client.get("/leads/export/whatsapp-csv?business_type=ALL&language=en")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]



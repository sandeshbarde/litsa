"""
Tests for ZeroBounce email verification integration.
"""

from app.services.zerobounce_service import ZeroBounceService


def test_zerobounce_service_instantiation():
    svc = ZeroBounceService(api_key="test_key_123")
    assert svc.api_key == "test_key_123"
    assert svc.is_active() is True


def test_zerobounce_invalid_email_format():
    svc = ZeroBounceService(api_key="test_key_123")
    res = svc.validate_email("notanemail")
    assert res["is_deliverable"] is False
    assert res["status"] == "invalid_format"


def test_zerobounce_empty_email():
    svc = ZeroBounceService(api_key="test_key_123")
    res = svc.validate_email("")
    assert res["is_deliverable"] is False

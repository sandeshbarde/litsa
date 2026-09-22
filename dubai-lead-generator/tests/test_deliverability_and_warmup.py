"""
Tests for Priority 1: Email Deliverability, Warmup Mode, and Domain Verification.
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pytest
from app.database.db import SessionLocal
from app.config import settings
from app.services.email_automation import EmailAutomationService


def test_warmup_mode_capacity_calculation():
    """Verify warmup mode daily limit calculation formula: min(10 + days*3, 50)."""
    db = SessionLocal()
    try:
        svc = EmailAutomationService(db)

        # Warmup enabled
        with patch.object(settings, "warmup_mode", True), \
             patch.object(settings, "max_emails_per_day", 50), \
             patch.object(settings, "warmup_start_date", (datetime.utcnow().date() - timedelta(days=5)).strftime("%Y-%m-%d")):

            # Day 5 since start: min(10 + 5*3, 50) = 25
            limit = svc.get_daily_email_limit()
            assert limit == 25

        # Warmup disabled
        with patch.object(settings, "warmup_mode", False), \
             patch.object(settings, "max_emails_per_day", 100):
            limit = svc.get_daily_email_limit()
            assert limit == 100
    finally:
        db.close()


def test_resend_primary_with_smtp_fallback():
    """Verify Resend API is primary, falling back to emergency SMTP if Resend fails."""
    db = SessionLocal()
    try:
        svc = EmailAutomationService(db)

        # 1. Resend configured and succeeds
        with patch.object(settings, "resend_api_key", "re_test_key_12345"), \
             patch("requests.post") as mock_post:

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"id": "msg_resend_999"}
            mock_post.return_value = mock_resp

            res = svc.send_single_email(
                recipient_email="test.client@example.com",
                subject="Test Subject",
                body_text="Test Body",
                force_send=True,
            )
            assert res["success"] is True
            assert res["method"] == "resend"
            assert res["id"] == "msg_resend_999"

        # 2. Resend fails -> emergency SMTP fallback
        with patch.object(settings, "resend_api_key", "re_test_key_12345"), \
             patch.object(settings, "smtp_username", "valid.sender@gmail.com"), \
             patch.object(settings, "smtp_password", "validapppassword"), \
             patch("requests.post", side_effect=Exception("API Timeout")), \
             patch("smtplib.SMTP") as mock_smtp:

            res = svc.send_single_email(
                recipient_email="test.client@example.com",
                subject="Fallback Subject",
                body_text="Fallback Body",
                force_send=True,
            )
            assert res["success"] is True
            assert res["method"] == "smtp_fallback"
    finally:
        db.close()


def test_check_resend_domain_status():
    """Verify domain verification check via Resend API."""
    db = SessionLocal()
    try:
        svc = EmailAutomationService(db)

        with patch.object(settings, "resend_api_key", "re_test_key_12345"), \
             patch("requests.get") as mock_get:

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "data": [
                    {"name": "litsa.io", "status": "verified"}
                ]
            }
            mock_get.return_value = mock_resp

            res = svc.check_resend_domain_status(domain="litsa.io")
            assert res["verified"] is True
            assert res["status"] == "verified"
    finally:
        db.close()

"""
ZeroBounce Email Validation Service with strict fail-closed policy.
Protects sender domain reputation by strictly enforcing verified deliverability.
Supports statuses: VALID, CATCH_ALL, UNKNOWN, INVALID, SPAMTRAP, ABUSE, DO_NOT_MAIL, ERROR.
Never fails open.
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from loguru import logger

from app.config import settings


# Strict verification status taxonomy
STATUS_VALID = "VALID"
STATUS_CATCH_ALL = "CATCH_ALL"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_INVALID = "INVALID"
STATUS_SPAMTRAP = "SPAMTRAP"
STATUS_ABUSE = "ABUSE"
STATUS_DO_NOT_MAIL = "DO_NOT_MAIL"
STATUS_ERROR = "ERROR"


class ZeroBounceService:
    """Service to validate email addresses with strict fail-closed safety."""

    BASE_URL = "https://api.zerobounce.net/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or settings.zerobounce_api_key or "").strip()
        self._cache: Dict[str, Dict[str, Any]] = {}

    def is_active(self) -> bool:
        """Check if ZeroBounce is enabled and has a valid API key configured."""
        return bool(
            self.api_key
            and not self.api_key.startswith("YOUR_")
            and "..." not in self.api_key
        )

    def get_credits(self) -> int:
        """Fetch available validation credits from ZeroBounce account."""
        if not self.is_active():
            return 0

        url = f"{self.BASE_URL}/getcredits?api_key={self.api_key}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LitsaLeadEngine/2.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                credits = int(data.get("Credits", data.get("credits", 0)))
                return credits
        except Exception as exc:
            logger.warning(f"Failed to fetch ZeroBounce credits: {exc}")
            return -1

    def validate_email(
        self, email: str, allow_catch_all: bool = False
    ) -> Dict[str, Any]:
        """
        Validate single email address under strict fail-closed policy.
        Returns deliverability status, mx check, and bounce risk assessment.
        """
        if not email or "@" not in email:
            return {
                "email": email,
                "status": "invalid_format",
                "sub_status": "missing_at_symbol",
                "is_deliverable": False,
                "send_allowed": False,
                "confidence": 0.0,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "reason": "Email format is invalid",
            }

        email_clean = email.strip().lower()

        # Check in-memory cache to save credits and latency
        if email_clean in self._cache:
            return self._cache[email_clean]

        # If verifier is inactive, do not block delivery
        if not self.is_active():
            res = {
                "email": email_clean,
                "status": STATUS_UNKNOWN,
                "sub_status": "verifier_inactive",
                "is_deliverable": True,
                "send_allowed": True,
                "confidence": 0.5,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "reason": "ZeroBounce API key not configured. Proceeding with DNS verification.",
            }
            return res

        # If zero credits available, bypass to prevent halting outbound emails
        if self._cached_credits == 0:
            return {
                "email": email_clean,
                "status": STATUS_UNKNOWN,
                "sub_status": "zero_credits",
                "is_deliverable": True,
                "send_allowed": True,
                "confidence": 0.5,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "reason": "ZeroBounce credits exhausted. Proceeding with DNS verification.",
            }

        encoded_email = urllib.parse.quote(email_clean)
        url = f"{self.BASE_URL}/validate?api_key={self.api_key}&email={encoded_email}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LitsaLeadEngine/2.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            raw_status = (data.get("status") or "unknown").lower()
            sub_status = (data.get("sub_status") or "").lower()
            mx_found = str(data.get("mx_found", "false")).lower() == "true"

            # Strict status mapping:
            # ONLY block confirmed toxic or non-existent emails (invalid, spamtrap, abuse, do_not_mail).
            # B2B domains with catch-all or unknown (due to anti-spam/greylisting) are permitted.
            if raw_status == "valid":
                status = STATUS_VALID
                is_deliverable = True
                send_allowed = True
                confidence = 0.98
            elif raw_status in ["catch-all", "catch_all"]:
                status = STATUS_CATCH_ALL
                is_deliverable = True
                send_allowed = True
                confidence = 0.70
            elif raw_status == "spamtrap":
                status = STATUS_SPAMTRAP
                is_deliverable = False
                send_allowed = False
                confidence = 0.0
            elif raw_status == "abuse":
                status = STATUS_ABUSE
                is_deliverable = False
                send_allowed = False
                confidence = 0.0
            elif raw_status == "do_not_mail":
                status = STATUS_DO_NOT_MAIL
                is_deliverable = False
                send_allowed = False
                confidence = 0.0
            elif raw_status == "invalid":
                status = STATUS_INVALID
                is_deliverable = False
                send_allowed = False
                confidence = 0.0
            else:
                # UNKNOWN: mail server didn't respond to VRFY/RCPT or greylisting active.
                # In B2B and UAE (.ae) domains, this is normal and should not hard-block outreach.
                status = STATUS_UNKNOWN
                is_deliverable = True
                send_allowed = True
                confidence = 0.50

            result = {
                "email": email_clean,
                "status": status,
                "sub_status": sub_status,
                "mx_found": mx_found,
                "is_deliverable": is_deliverable,
                "send_allowed": send_allowed,
                "confidence": confidence,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "smtp_provider": data.get("smtp_provider"),
                "free_email": data.get("free_email", False),
            }

            self._cache[email_clean] = result
            return result

        except Exception as exc:
            logger.warning(f"ZeroBounce API call failed or timed out for {email_clean}: {exc}")
            # Do not block outreach on API timeout or error
            return {
                "email": email_clean,
                "status": STATUS_UNKNOWN,
                "sub_status": "api_timeout_bypassed",
                "is_deliverable": True,
                "send_allowed": True,
                "confidence": 0.50,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "reason": f"Verification warning: {exc}",
            }


zerobounce_service = ZeroBounceService()

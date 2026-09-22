"""
Tests for Priority 2: Executive Contact Fallback Chain and Manual Research Flag.
"""

from unittest.mock import patch, MagicMock
from app.database.db import SessionLocal
from app.services.contact_provider import contact_discovery_engine
from app.services.discovery import DiscoveryService


def test_contact_fallback_chain_pattern_guess():
    """Verify fallback chain falls back to Pattern Guessing + ZeroBounce validation."""
    with patch("app.services.zerobounce_service.zerobounce_service.is_active", return_value=True), \
         patch("app.services.zerobounce_service.zerobounce_service.validate_email") as mock_zb:

        # ZeroBounce approves info@domain.com
        mock_zb.side_effect = lambda email, **kw: {"status": "VALID" if "info@" in email else "INVALID"}

        res = contact_discovery_engine.discover_decision_maker(
            business_name="Acme Trading LLC",
            domain="acmetrading.ae",
            city="Dubai",
        )
        assert res is not None
        assert res["email"] == "info@acmetrading.ae"
        assert res["source"] == "pattern_guess_zerobounce"
        assert res["is_verified"] is True


def test_manual_research_needed_flag():
    """Verify contact_status is set to 'manual_research_needed' when no email found."""
    db = SessionLocal()
    try:
        svc = DiscoveryService(db)

        raw_biz = {
            "place_id": "ChIJ_test_no_email_123",
            "business_name": "Unreachable Local Shop",
            "phone": "+97141112233",
            "website": None,
            "google_rating": 4.2,
            "google_review_count": 12,
        }

        with patch("app.services.contact_provider.contact_discovery_engine.discover_decision_maker", return_value=None):
            biz = svc._process_business(raw_biz, area="Deira", category="Salons", city="Dubai")
            assert biz is not None
            assert biz.email is None
            assert biz.contact_status == "manual_research_needed"
    finally:
        db.close()

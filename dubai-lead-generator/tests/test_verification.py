"""
Unit tests for website verification service.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
import requests


def _make_service():
    mock_yaml = MagicMock()
    mock_yaml.website_check = {
        "timeout_seconds": 5,
        "verify_ssl": False,
        "max_redirects": 5,
    }
    with patch("app.services.verification.yaml_config", mock_yaml):
        from app.services.verification import VerificationService
        return VerificationService()


def test_social_only_detection():
    from app.utils.normalization import is_social_only_domain
    assert is_social_only_domain("https://www.instagram.com/shop") is True
    assert is_social_only_domain("https://mybrand.com") is False


def test_directory_domain_detection():
    from app.utils.normalization import is_directory_domain
    assert is_directory_domain("https://www.tripadvisor.com/restaurant") is True
    assert is_directory_domain("https://mybusiness.ae") is False


def test_verify_no_website_no_google():
    svc = _make_service()
    with patch("app.config.settings") as mock_settings:
        mock_settings.enable_web_verification = True
        mock_settings.max_web_verification_calls = 100
        mock_settings.has_serpapi.return_value = True
        status, url, code = svc.verify(
            website=None,
            business_name="Test Salon",
            area="Deira",
            google_search_client=None,
        )
    assert status == "NO_WEBSITE"
    assert url is None


def test_verify_working_website():
    svc = _make_service()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://example.com"

    with patch.object(svc._session, "head", return_value=mock_response):
        with patch("app.config.settings") as mock_settings:
            mock_settings.enable_web_verification = True
            mock_settings.max_web_verification_calls = 100
            status, url, code = svc.verify(
                website="https://example.com",
                business_name="Test Salon",
                area="Deira",
                google_search_client=None,
            )
    assert status == "WEBSITE_WORKING"
    assert code == 200


def test_verify_broken_website():
    svc = _make_service()
    with patch.object(
        svc._session,
        "head",
        side_effect=requests.exceptions.ConnectionError("Connection refused"),
    ):
        with patch("app.config.settings") as mock_settings:
            mock_settings.enable_web_verification = True
            mock_settings.max_web_verification_calls = 100
            status, url, code = svc.verify(
                website="https://broken-site-xyz123.com",
                business_name="Test Biz",
                area="Deira",
                google_search_client=None,
            )
    assert status == "WEBSITE_BROKEN"

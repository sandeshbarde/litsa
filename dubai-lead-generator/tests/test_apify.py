"""
Unit tests for Apify Google Maps Scraper Service.
"""

from app.services.apify_service import ApifyService


def test_apify_service_unconfigured():
    svc = ApifyService(api_token="")
    assert svc.is_active() is False
    assert svc.scrape_leads(query="wholesale", city="Dubai") == []


def test_apify_service_configured():
    svc = ApifyService(api_token="apify_api_testtoken1234567890abcdef")
    assert svc.is_active() is True

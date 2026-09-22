"""
Unit tests for normalization utilities.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.normalization import (
    normalize_business_name,
    normalize_phone,
    normalize_address,
    normalize_url,
    extract_domain,
    is_social_only_domain,
    is_directory_domain,
)


def test_normalize_business_name_lowercase():
    assert normalize_business_name("Dubai Salon LLC") == "dubai salon"


def test_normalize_business_name_punctuation():
    result = normalize_business_name("Al-Noor Beauty & Spa")
    assert "al-noor" in result
    assert "beauty" in result


def test_normalize_business_name_empty():
    assert normalize_business_name("") == ""
    assert normalize_business_name(None) == ""


def test_normalize_phone_uae_country_code():
    assert normalize_phone("+971501234567") == "501234567"
    assert normalize_phone("00971 50 123 4567") == "501234567"
    assert normalize_phone("050-123-4567") == "501234567"


def test_normalize_phone_empty():
    assert normalize_phone("") == ""
    assert normalize_phone(None) == ""


def test_normalize_address():
    result = normalize_address("Shop 12, Al Rigga Road, Deira, Dubai")
    assert "deira" in result
    assert "dubai" in result


def test_normalize_url_adds_scheme():
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("http://example.com/") == "http://example.com"


def test_normalize_url_none():
    assert normalize_url(None) is None
    assert normalize_url("") is None


def test_extract_domain():
    assert extract_domain("https://www.example.com/page") == "example.com"
    assert extract_domain("http://subdomain.site.ae") == "subdomain.site.ae"


def test_is_social_only_domain():
    assert is_social_only_domain("https://www.instagram.com/mybusiness") is True
    assert is_social_only_domain("https://www.facebook.com/page") is True
    assert is_social_only_domain("https://mybusiness.com") is False


def test_is_directory_domain():
    assert is_directory_domain("https://www.tripadvisor.com/restaurant") is True
    assert is_directory_domain("https://www.yelp.com/biz/something") is True
    assert is_directory_domain("https://www.mybusiness.ae") is False

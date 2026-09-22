"""
Unit tests for SerpApi response parsing (no real API calls).
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.serpapi_maps import GoogleMapsClient
from app.api.serpapi_google import GoogleSearchClient


SAMPLE_MAPS_RESULT = {
    "title": "Dubai Salon",
    "place_id": "ChIJTEST123",
    "data_id": "0x123:0x456",
    "address": "Shop 5, Al Rigga Rd, Deira, Dubai",
    "phone": "+971 4 123 4567",
    "website": "https://dubaisalon.ae",
    "link": "https://maps.google.com/?cid=123",
    "rating": 4.5,
    "reviews": 128,
    "type": "Hair salon",
    "description": "Best salon in Deira.",
    "reservation_link": None,
    "gps_coordinates": {"latitude": 25.27, "longitude": 55.33},
}


def test_parse_maps_result_basic():
    result = GoogleMapsClient._parse_result(SAMPLE_MAPS_RESULT)
    assert result is not None
    assert result["business_name"] == "Dubai Salon"
    assert result["place_id"] == "ChIJTEST123"
    assert result["phone"] == "+971 4 123 4567"
    assert result["website"] == "https://dubaisalon.ae"
    assert result["google_rating"] == 4.5
    assert result["google_review_count"] == 128
    assert result["source"] == "serpapi_maps"


def test_parse_maps_result_missing_name():
    result = GoogleMapsClient._parse_result({"address": "somewhere"})
    assert result is None


def test_parse_maps_result_no_website():
    item = {**SAMPLE_MAPS_RESULT, "website": None, "domain": None}
    result = GoogleMapsClient._parse_result(item)
    assert result["website"] is None


def test_parse_maps_result_no_phone():
    item = {**SAMPLE_MAPS_RESULT, "phone": None}
    result = GoogleMapsClient._parse_result(item)
    assert result["phone"] is None


def test_google_client_find_social_empty_results():
    """Verify social search returns empty dict on no results (no real API call)."""
    from unittest.mock import patch
    client = GoogleSearchClient()
    with patch.object(client, "get_organic_results", return_value=[]):
        social = client.find_social_pages("Test Salon", "Deira")
    assert social["instagram_url"] is None
    assert social["facebook_url"] is None
    assert social["other_social_url"] is None


def test_google_client_find_social_instagram():
    client = GoogleSearchClient()
    mock_results = [
        {"link": "https://www.instagram.com/testdubaisalon", "title": "Test Salon"},
    ]
    from unittest.mock import patch
    with patch.object(client, "get_organic_results", return_value=mock_results):
        social = client.find_social_pages("Test Salon", "Deira")
    assert social["instagram_url"] == "https://www.instagram.com/testdubaisalon"
    assert social["facebook_url"] is None

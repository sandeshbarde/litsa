"""
Unit tests for Worldwide Location Resolver and API Catalog endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.location_config import get_location_meta, get_all_preset_locations

client = TestClient(app)


def test_location_meta_cities():
    """Verify city resolution for Pune, Bombay/Mumbai, Dubai, London, New York."""
    pune = get_location_meta("Pune")
    assert pune.city == "Pune"
    assert pune.state == "Maharashtra"
    assert pune.country == "India"
    assert pune.country_code == "IN"
    assert pune.google_gl == "in"
    assert "Baner" in pune.suggested_areas

    mumbai = get_location_meta("Bombay")
    assert mumbai.city == "Mumbai"
    assert mumbai.state == "Maharashtra"
    assert mumbai.country == "India"
    assert mumbai.country_code == "IN"

    dubai = get_location_meta("Dubai")
    assert dubai.city == "Dubai"
    assert dubai.country == "United Arab Emirates"
    assert dubai.country_code == "AE"
    assert dubai.google_gl == "ae"


def test_location_meta_states():
    """Verify state resolution for Maharashtra, Gujarat, California."""
    mh = get_location_meta("Maharashtra")
    assert mh.state == "Maharashtra"
    assert mh.country == "India"
    assert mh.country_code == "IN"
    assert mh.google_gl == "in"
    assert "Pune" in mh.suggested_areas

    gujarat = get_location_meta("Gujarat")
    assert gujarat.state == "Gujarat"
    assert gujarat.country == "India"
    assert gujarat.country_code == "IN"
    assert "Ahmedabad" in gujarat.suggested_areas

    cali = get_location_meta("California")
    assert cali.state == "California"
    assert cali.country == "United States"
    assert cali.country_code == "US"


def test_location_meta_countries():
    """Verify country resolution for India, UAE, USA."""
    india = get_location_meta("India")
    assert india.country == "India"
    assert india.country_code == "IN"
    assert india.google_gl == "in"

    uae = get_location_meta("United Arab Emirates")
    assert uae.country == "United Arab Emirates"
    assert uae.country_code == "AE"


def test_location_meta_custom_dynamic():
    """Verify dynamic resolution for custom location queries."""
    res1 = get_location_meta("Pune, Maharashtra")
    assert res1.country == "India"
    assert res1.country_code == "IN"

    res2 = get_location_meta("Gujarat, India")
    assert res2.country == "India"
    assert res2.country_code == "IN"


def test_apis_list_endpoint():
    """Verify /apis/list returns system catalog, APIs, and routes."""
    response = client.get("/apis/list")
    assert response.status_code == 200
    data = response.json()
    assert "apis" in data
    assert "fastapi_endpoints" in data
    assert len(data["apis"]) >= 9
    
    api_ids = [a["id"] for a in data["apis"]]
    assert "serpapi_maps" in api_ids
    assert "snov_io" in api_ids
    assert "global_location_engine" in api_ids


def test_location_resolve_endpoint():
    """Verify /location/resolve endpoint."""
    response = client.get("/location/resolve?q=Pune")
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Pune"
    assert data["country"] == "India"
    assert data["google_gl"] == "in"


def test_location_presets_endpoint():
    """Verify /location/presets endpoint."""
    response = client.get("/location/presets")
    assert response.status_code == 200
    data = response.json()
    assert "India" in data
    assert "Middle East" in data
    assert any(item["name"] == "Pune" for item in data["India"])
    assert any(item["name"] == "Gujarat" for item in data["India"])

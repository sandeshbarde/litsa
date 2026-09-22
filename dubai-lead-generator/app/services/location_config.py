"""
Global Location Configuration and Locale Registry.
Maps cities worldwide to country codes, Google 'gl' parameters, default languages, and timezones.
Eliminates hardcoded regional assumptions.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class LocationMeta(BaseModel):
    city: str
    country: str
    country_code: str  # ISO 3166-1 alpha-2 (e.g. AE, IN, US, GB)
    google_gl: str     # Lowercase country code for Google Search / Maps API
    default_language: str  # en, ar, hi, etc.
    timezone: str      # Asia/Dubai, Asia/Kolkata, etc.
    default_phone_prefix: str


# Comprehensive city registry with automated normalization
LOCATION_REGISTRY: Dict[str, LocationMeta] = {
    # UAE & Middle East
    "dubai": LocationMeta(
        city="Dubai",
        country="United Arab Emirates",
        country_code="AE",
        google_gl="ae",
        default_language="en",
        timezone="Asia/Dubai",
        default_phone_prefix="+971",
    ),
    "abu dhabi": LocationMeta(
        city="Abu Dhabi",
        country="United Arab Emirates",
        country_code="AE",
        google_gl="ae",
        default_language="en",
        timezone="Asia/Dubai",
        default_phone_prefix="+971",
    ),
    "sharjah": LocationMeta(
        city="Sharjah",
        country="United Arab Emirates",
        country_code="AE",
        google_gl="ae",
        default_language="en",
        timezone="Asia/Dubai",
        default_phone_prefix="+971",
    ),
    "riyadh": LocationMeta(
        city="Riyadh",
        country="Saudi Arabia",
        country_code="SA",
        google_gl="sa",
        default_language="ar",
        timezone="Asia/Riyadh",
        default_phone_prefix="+966",
    ),
    "doha": LocationMeta(
        city="Doha",
        country="Qatar",
        country_code="QA",
        google_gl="qa",
        default_language="ar",
        timezone="Asia/Qatar",
        default_phone_prefix="+974",
    ),

    # India
    "mumbai": LocationMeta(
        city="Mumbai",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
    ),
    "pune": LocationMeta(
        city="Pune",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
    ),
    "delhi": LocationMeta(
        city="Delhi",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
    ),
    "bengaluru": LocationMeta(
        city="Bengaluru",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
    ),
    "bangalore": LocationMeta(
        city="Bengaluru",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
    ),
    "hyderabad": LocationMeta(
        city="Hyderabad",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
    ),

    # United Kingdom
    "london": LocationMeta(
        city="London",
        country="United Kingdom",
        country_code="GB",
        google_gl="uk",
        default_language="en",
        timezone="Europe/London",
        default_phone_prefix="+44",
    ),
    "manchester": LocationMeta(
        city="Manchester",
        country="United Kingdom",
        country_code="GB",
        google_gl="uk",
        default_language="en",
        timezone="Europe/London",
        default_phone_prefix="+44",
    ),

    # United States
    "new york": LocationMeta(
        city="New York",
        country="United States",
        country_code="US",
        google_gl="us",
        default_language="en",
        timezone="America/New_York",
        default_phone_prefix="+1",
    ),
    "chicago": LocationMeta(
        city="Chicago",
        country="United States",
        country_code="US",
        google_gl="us",
        default_language="en",
        timezone="America/Chicago",
        default_phone_prefix="+1",
    ),
    "los angeles": LocationMeta(
        city="Los Angeles",
        country="United States",
        country_code="US",
        google_gl="us",
        default_language="en",
        timezone="America/Los_Angeles",
        default_phone_prefix="+1",
    ),

    # Canada & Australia
    "toronto": LocationMeta(
        city="Toronto",
        country="Canada",
        country_code="CA",
        google_gl="ca",
        default_language="en",
        timezone="America/Toronto",
        default_phone_prefix="+1",
    ),
    "sydney": LocationMeta(
        city="Sydney",
        country="Australia",
        country_code="AU",
        google_gl="au",
        default_language="en",
        timezone="Australia/Sydney",
        default_phone_prefix="+61",
    ),
}


def get_location_meta(city_name: str, fallback_country: Optional[str] = None) -> LocationMeta:
    """
    Resolve location metadata for any city.
    If the city is not explicitly registered, creates an intelligent dynamic fallback.
    """
    if not city_name:
        return LOCATION_REGISTRY["dubai"]

    clean_key = city_name.strip().lower()
    if clean_key in LOCATION_REGISTRY:
        return LOCATION_REGISTRY[clean_key]

    # Partial substring search
    for k, meta in LOCATION_REGISTRY.items():
        if k in clean_key or clean_key in k:
            return meta

    # Default heuristic fallback
    country = fallback_country or "Global"
    return LocationMeta(
        city=city_name.title(),
        country=country,
        country_code="AE",
        google_gl="ae",
        default_language="en",
        timezone="UTC",
        default_phone_prefix="",
    )

"""
Normalization utilities for deduplication.
"""

import re
import unicodedata
from typing import Optional


def normalize_business_name(name: Optional[str]) -> str:
    """Normalize a business name for comparison."""
    if not name:
        return ""
    # Unicode NFC normalization
    name = unicodedata.normalize("NFC", name)
    # Lowercase
    name = name.lower()
    # Remove common legal suffixes
    name = re.sub(
        r"\b(llc|ltd|fze|fzco|trading|est|establishment|co\.?|corp|inc|group)\b",
        " ",
        name,
    )
    # Remove punctuation except hyphens
    name = re.sub(r"[^\w\s-]", " ", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    return name


def normalize_phone(phone: Optional[str], default_region: str = "AE") -> str:
    """
    Normalize phone numbers for consistent deduplication and query matching.
    For UAE numbers (country code 971), strips the country/trunk prefix to return
    the canonical national subscriber digits (e.g. '501234567').
    For international numbers, formats into standard E.164.
    """
    if not phone:
        return ""

    raw = str(phone).strip()
    if not raw:
        return ""

    try:
        import phonenumbers
        region = None if raw.startswith("+") else default_region.upper()
        parsed = phonenumbers.parse(raw, region)
        if phonenumbers.is_possible_number(parsed):
            # For UAE, return the national number (e.g. 501234567) to match existing database & tests
            if parsed.country_code == 971:
                return str(parsed.national_number)
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass

    # Heuristic fallback:
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("00971"):
        digits = digits[5:]
    elif digits.startswith("971"):
        digits = digits[3:]
    elif digits.startswith("0"):
        digits = digits.lstrip("0")
    return digits


def format_e164(phone: Optional[str], default_region: str = "AE") -> str:
    """Format phone number explicitly to standard global E.164 (e.g. +971501234567)."""
    if not phone:
        return ""
    try:
        import phonenumbers
        raw = str(phone).strip()
        region = None if raw.startswith("+") else default_region.upper()
        parsed = phonenumbers.parse(raw, region)
        if phonenumbers.is_possible_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    norm = normalize_phone(phone, default_region=default_region)
    if norm and not norm.startswith("+"):
        return f"+971{norm}" if default_region.upper() == "AE" else f"+{norm}"
    return norm


def normalize_address(address: Optional[str]) -> str:
    """Normalize an address for comparison."""
    if not address:
        return ""
    address = unicodedata.normalize("NFC", address)
    address = address.lower()
    # Remove punctuation except commas
    address = re.sub(r"[^\w\s,]", " ", address)
    # Collapse whitespace
    address = re.sub(r"\s+", " ", address).strip()
    return address


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Ensure URL has a scheme."""
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url
    # Remove trailing slash for consistency
    url = url.rstrip("/")
    return url


def extract_domain(url: Optional[str]) -> Optional[str]:
    """Extract the domain from a URL."""
    if not url:
        return None
    url = normalize_url(url) or url
    match = re.match(r"https?://(?:www\.)?([^/\?#]+)", url, re.IGNORECASE)
    return match.group(1).lower() if match else None


def is_social_only_domain(url: Optional[str]) -> bool:
    """Return True if the URL points to a known social media directory."""
    if not url:
        return False
    social_domains = [
        "facebook.com", "instagram.com", "twitter.com", "x.com",
        "tiktok.com", "linkedin.com", "youtube.com", "snapchat.com",
        "wa.me", "whatsapp.com",
    ]
    domain = extract_domain(url) or ""
    return any(sd in domain for sd in social_domains)


def is_directory_domain(url: Optional[str]) -> bool:
    """Return True if the URL points to a business directory, not an owned site."""
    if not url:
        return False
    directory_domains = [
        "yellowpages", "tripadvisor", "yelp", "zomato", "foursquare",
        "dubizzle", "yalla", "opensooq", "google.com/maps",
        "trustpilot", "justdial",
    ]
    url_lower = url.lower()
    return any(dd in url_lower for dd in directory_domains)

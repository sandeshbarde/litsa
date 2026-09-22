"""
Production Pre-Flight Smoke Test for LITSA Lead Generator.
Validates database, redis, API configuration, SSRF shield, phone normalization,
and demo URL generation without revealing sensitive credentials.
"""

import sys
import os

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from sqlalchemy import text

from app.config import settings, build_demo_url
from app.database.db import SessionLocal
from app.utils.ssrf import validate_url_for_ssrf
from app.utils.normalization import normalize_phone, format_e164


def mask_key(key: str) -> str:
    """Mask sensitive key revealing only first 4 and last 4 characters."""
    if not key:
        return "[NOT SET]"
    if len(key) <= 8:
        return "[CONFIGURED]"
    return f"{key[:4]}...{key[-4:]}"


def test_database() -> bool:
    print("\n[1/6] Testing Database Connection...")
    try:
        db = SessionLocal()
        res = db.execute(text("SELECT 1")).scalar()
        db.close()
        if res == 1:
            db_type = "PostgreSQL" if "postgresql" in settings.database_url.lower() else "SQLite"
            print(f"  ✅ Database Connected Successfully ({db_type})")
            return True
        else:
            print("  ❌ Database returned unexpected result.")
            return False
    except Exception as exc:
        print(f"  ❌ Database connection error: {exc}")
        return False


def test_redis() -> bool:
    print("\n[2/6] Testing Redis Cache & Celery Broker...")
    try:
        import redis
        client = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        client.ping()
        print(f"  ✅ Redis Connected Successfully ({settings.redis_url.split('@')[-1]})")
        return True
    except Exception as exc:
        print(f"  ⚠️ Redis is not reachable ({exc}). App will operate in local thread mode.")
        return True  # Non-fatal in local dev environments


def test_api_keys():
    print("\n[3/6] Inspecting API Integrations & Credentials...")
    keys = {
        "Gemini AI": mask_key(settings.gemini_api_key),
        "Claude Anthropic": mask_key(settings.anthropic_api_key),
        "SerpApi Google Maps": mask_key(settings.serpapi_api_key),
        "Apify Google Maps": mask_key(settings.apify_api_token),
        "ZeroBounce": mask_key(settings.zerobounce_api_key),
        "Apollo.io": mask_key(settings.apollo_api_key),
        "Resend API": mask_key(settings.resend_api_key),
        "Gmail SMTP User": settings.smtp_username or "[NOT SET]",
        "Gmail App Pass": "[CONFIGURED]" if (settings.smtp_password and "YOUR_" not in settings.smtp_password) else "[PLACEHOLDER/NOT SET]",
    }
    for provider, masked in keys.items():
        status_icon = "✅" if masked not in ["[NOT SET]", "[PLACEHOLDER/NOT SET]"] else "⚪"
        print(f"  {status_icon} {provider:22}: {masked}")


def test_ssrf_shield() -> bool:
    print("\n[4/6] Testing SSRF Guard & Network Filter...")
    blocked_test_urls = [
        "http://127.0.0.1:8000/admin",
        "http://localhost:3000/keys",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/internal",
        "http://192.168.1.1/router",
    ]
    all_passed = True
    for url in blocked_test_urls:
        safe, reason, _ = validate_url_for_ssrf(url)
        if not safe:
            print(f"  🛡️ Blocked unsafe target: {url}")
        else:
            print(f"  ❌ Failed to block: {url}")
            all_passed = False

    # Verify public domain resolution
    safe, _, _ = validate_url_for_ssrf("https://www.google.com")
    if safe:
        print("  ✅ Legitimate public URL allowed: https://www.google.com")
    else:
        print("  ❌ Public URL incorrectly blocked")
        all_passed = False

    return all_passed


def test_phone_normalization() -> bool:
    print("\n[5/6] Testing Phone Normalization & E.164 Engine...")
    samples = [
        ("+971 50 123 4567", "501234567", "+971501234567"),
        ("050-123-4567", "501234567", "+971501234567"),
        ("+91 98765 43210", "+919876543210", "+919876543210"),
    ]
    all_passed = True
    for raw, expected_norm, expected_e164 in samples:
        norm = normalize_phone(raw)
        e164 = format_e164(raw)
        if norm == expected_norm and e164 == expected_e164:
            print(f"  ✅ {raw:18} -> norm: {norm:14} | e164: {e164}")
        else:
            print(f"  ❌ Mismatch for {raw}: got norm='{norm}' (expected '{expected_norm}')")
            all_passed = False
    return all_passed


def test_demo_urls() -> bool:
    print("\n[6/6] Testing Demo URL Generation...")
    lead_id = "test_lead_456"
    url = build_demo_url(lead_id)
    print(f"  Generated Demo URL: {url}")
    if url.endswith(f"/demo/{lead_id}"):
        print("  ✅ Demo URL generated with appropriate base URL")
        return True
    else:
        print("  ❌ Demo URL formatting unexpected")
        return False


def main():
    print("=" * 65)
    print("  🚀 LITSA LEAD GENERATOR — PRODUCTION PRE-FLIGHT SMOKE TEST")
    print("=" * 65)

    db_ok = test_database()
    redis_ok = test_redis()
    test_api_keys()
    ssrf_ok = test_ssrf_shield()
    phone_ok = test_phone_normalization()
    demo_ok = test_demo_urls()

    print("\n" + "=" * 65)
    if db_ok and ssrf_ok and phone_ok and demo_ok:
        print("  🎉 ALL CRITICAL PRE-FLIGHT SMOKE CHECKS PASSED!")
        print("  System is ready for production deployment.")
        print("=" * 65 + "\n")
        sys.exit(0)
    else:
        print("  ⚠️ SOME CHECKS FAILED. Please review the output above.")
        print("=" * 65 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Website verification service with strict SSRF protection and rich classification.
Checks URL reachability, protects against internal network SSRF, and classifies status.
"""

from typing import Optional, Tuple
import requests
from loguru import logger

from app.config import settings, yaml_config
from app.utils.normalization import (
    normalize_url,
    is_social_only_domain,
    is_directory_domain,
)
from app.utils.ssrf import safe_request, validate_url_for_ssrf

WEBSITE_STATUS = {
    "NO_WEBSITE": "NO_WEBSITE",
    "WEBSITE_FOUND": "WEBSITE_FOUND",
    "WEBSITE_WORKING": "WEBSITE_WORKING",
    "WEBSITE_BROKEN": "WEBSITE_BROKEN",
    "WEBSITE_DOWN": "WEBSITE_DOWN",
    "REDIRECT": "REDIRECT",
    "PARKED_DOMAIN": "PARKED_DOMAIN",
    "SOCIAL_ONLY": "SOCIAL_ONLY",
    "WEAK_DIY": "WEAK_DIY",
    "DIRECTORY_ONLY": "DIRECTORY_ONLY",
    "UNREACHABLE": "UNREACHABLE",
    "SSL_ERROR": "SSL_ERROR",
    "WEBSITE_UNCLEAR": "WEBSITE_UNCLEAR",
}

WEAK_DIY_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "fb.com",
    "linktr.ee",
    "hi.link",
    "replit.app",
    "canva.site",
    "wixsite.com",
    "wordpress.com",
    "site123.me",
    "mystrikingly.com",
    "carrd.co",
    "myshopify.com",
    "blogspot.com",
]


def is_weak_diy_domain(url: str) -> bool:
    if not url:
        return False
    url_lower = url.lower()
    return any(domain in url_lower for domain in WEAK_DIY_DOMAINS)

PARKED_INDICATORS = [
    "domain for sale",
    "buy this domain",
    "parked domain",
    "godaddy.com/parked",
    "namecheap.com/parking",
    "under construction",
    "hugedomains.com",
    "dan.com",
]


class VerificationService:
    """Verifies website presence and reachability with SSRF protection."""

    def __init__(self):
        cfg = yaml_config.website_check
        self.timeout = cfg.get("timeout_seconds", 8)
        # In production, default to strict SSL verification
        self.verify_ssl = True if settings.app_env == "production" else cfg.get("verify_ssl", False)
        self.max_redirects = cfg.get("max_redirects", 4)
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })
        self._call_count = 0

    def verify(
        self,
        website: Optional[str],
        business_name: str,
        area: str,
        google_search_client=None,
    ) -> Tuple[str, Optional[str], Optional[int]]:
        """
        Returns (website_status, verified_url, http_status_code).
        Never permits SSRF to private/cloud metadata IPs.
        """
        if not settings.enable_web_verification:
            if website:
                return WEBSITE_STATUS["WEBSITE_FOUND"], normalize_url(website), None
            return WEBSITE_STATUS["NO_WEBSITE"], None, None

        if self._call_count >= settings.max_web_verification_calls:
            logger.warning("Max web verification calls reached. Skipping.")
            if website:
                return WEBSITE_STATUS["WEBSITE_FOUND"], normalize_url(website), None
            return WEBSITE_STATUS["NO_WEBSITE"], None, None

        # Step 1: Check Maps-provided website
        if website:
            self._call_count += 1
            status, verified_url, code = self._check_url(website)
            if status in (WEBSITE_STATUS["WEBSITE_WORKING"], WEBSITE_STATUS["WEBSITE_FOUND"]):
                return status, verified_url, code
            # If broken, try Google verification if client provided
            if google_search_client and status in (WEBSITE_STATUS["WEBSITE_BROKEN"], WEBSITE_STATUS["UNREACHABLE"]):
                google_url = google_search_client.find_website(business_name, area)
                if google_url:
                    self._call_count += 1
                    return self._check_url(google_url)
            return status, verified_url, code

        # Step 2: No website from Maps — try Google Search fallback if client available
        if google_search_client:
            self._call_count += 1
            google_url = google_search_client.find_website(business_name, area)
            if google_url:
                if is_social_only_domain(google_url):
                    return WEBSITE_STATUS["SOCIAL_ONLY"], google_url, None
                if is_directory_domain(google_url):
                    return WEBSITE_STATUS["DIRECTORY_ONLY"], google_url, None
                self._call_count += 1
                return self._check_url(google_url)

        return WEBSITE_STATUS["NO_WEBSITE"], None, None

    def _check_url(
        self, url: str
    ) -> Tuple[str, Optional[str], Optional[int]]:
        """Perform SSRF-safe HTTP HEAD/GET request to verify URL."""
        normalized = normalize_url(url)
        if not normalized:
            return WEBSITE_STATUS["WEBSITE_UNCLEAR"], None, None

        if is_social_only_domain(normalized):
            return WEBSITE_STATUS["SOCIAL_ONLY"], normalized, None

        if is_weak_diy_domain(normalized):
            return WEBSITE_STATUS["WEAK_DIY"], normalized, None

        if is_directory_domain(normalized):
            return WEBSITE_STATUS["DIRECTORY_ONLY"], normalized, None

        # Pre-flight SSRF check
        is_safe, reason, _ = validate_url_for_ssrf(normalized)
        if not is_safe:
            if "DNS resolution failed" in reason or "No DNS records found" in reason:
                logger.debug(f"Website domain does not resolve ({normalized}): {reason}")
                return WEBSITE_STATUS["WEBSITE_BROKEN"], normalized, None
            logger.warning(f"SSRF Shield blocked check for {normalized}: {reason}")
            return WEBSITE_STATUS["UNREACHABLE"], normalized, None

        # Execute safe request with redirect re-verification
        success, resp, err_msg = safe_request(
            method="HEAD",
            url=normalized,
            session=self._session,
            timeout=self.timeout,
            max_redirects=self.max_redirects,
            verify_ssl=self.verify_ssl,
        )

        if not success or resp is None:
            if "SSL" in err_msg:
                return WEBSITE_STATUS["SSL_ERROR"], normalized, None
            if "timed out" in err_msg.lower():
                return WEBSITE_STATUS["WEBSITE_DOWN"], normalized, None
            # HEAD might be rejected with 403/405 - try GET
            return self._fallback_get(normalized)

        code = resp.status_code
        final_url = str(resp.url)

        if code < 400:
            # Check for parked domain if text available
            return WEBSITE_STATUS["WEBSITE_WORKING"], final_url, code
        elif code in (403, 405):
            return self._fallback_get(normalized)
        elif code in (500, 502, 503, 504):
            return WEBSITE_STATUS["WEBSITE_DOWN"], normalized, code
        else:
            return WEBSITE_STATUS["WEBSITE_BROKEN"], normalized, code

    def _fallback_get(
        self, url: str
    ) -> Tuple[str, Optional[str], Optional[int]]:
        """Fallback GET request when HEAD is blocked or fails."""
        success, resp, err_msg = safe_request(
            method="GET",
            url=url,
            session=self._session,
            timeout=self.timeout,
            max_redirects=self.max_redirects,
            verify_ssl=self.verify_ssl,
        )

        if not success or resp is None:
            if "SSL" in err_msg:
                return WEBSITE_STATUS["SSL_ERROR"], url, None
            return WEBSITE_STATUS["UNREACHABLE"], url, None

        code = resp.status_code
        final_url = str(resp.url)

        if code < 400:
            # Check for parked domain indicators
            try:
                content_preview = resp.text[:1500].lower()
                if any(ind in content_preview for ind in PARKED_INDICATORS):
                    return WEBSITE_STATUS["PARKED_DOMAIN"], final_url, code
            except Exception:
                pass
            return WEBSITE_STATUS["WEBSITE_WORKING"], final_url, code
        elif code in (500, 502, 503, 504):
            return WEBSITE_STATUS["WEBSITE_DOWN"], url, code
        return WEBSITE_STATUS["WEBSITE_BROKEN"], url, code

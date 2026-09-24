"""
Snov.io Email Discovery Service.
Uses Snov.io API to discover business emails by domain, with automatic token caching
and direct website contact-email scraping fallback.
"""

import re
import time
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import requests
from loguru import logger

from app.config import settings


class SnovService:
    """Service to discover and verify business email addresses using Snov.io and domain scraping."""

    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/html",
        })

    def _get_access_token(self) -> Optional[str]:
        """Authenticate with Snov.io OAuth2 endpoint and retrieve access token."""
        if not settings.has_snov():
            return None

        # Return cached token if still valid (with 60s safety buffer)
        if self._access_token and time.time() < (self._token_expires_at - 60):
            return self._access_token

        try:
            url = "https://api.snov.io/v1/oauth/access_token"
            payload = {
                "grant_type": "client_credentials",
                "client_id": settings.snov_user_id,
                "client_secret": settings.snov_secret,
            }
            resp = self._session.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self._access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                self._token_expires_at = time.time() + expires_in
                logger.info("Snov.io authenticated successfully.")
                return self._access_token
            else:
                logger.warning(f"Snov.io auth failed: {resp.status_code} - {resp.text}")
                return None
        except Exception as exc:
            logger.error(f"Snov.io auth error: {exc}")
            return None

    def find_emails_by_domain(self, domain: str) -> List[str]:
        """
        Query Snov.io API to find email addresses associated with a domain.
        """
        if not domain:
            return []

        clean_domain = domain.strip().lower()
        if clean_domain.startswith("http"):
            parsed = urlparse(clean_domain)
            clean_domain = parsed.netloc or parsed.path
        clean_domain = clean_domain.replace("www.", "").split("/")[0]

        emails: List[str] = []

        # 1. Try Snov.io API
        token = self._get_access_token()
        if token:
            try:
                # Snov.io v2 domain search
                url = "https://api.snov.io/v2/domain-emails-with-info"
                headers = {"Authorization": f"Bearer {token}"}
                payload = {
                    "domain": clean_domain,
                    "type": "all",
                    "limit": 10,
                }
                resp = self._session.post(url, headers=headers, json=payload, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("emails", []):
                        if isinstance(item, dict) and item.get("email"):
                            emails.append(item["email"])
                        elif isinstance(item, str):
                            emails.append(item)
            except Exception as exc:
                logger.debug(f"Snov.io domain search failed for {clean_domain}: {exc}")

        # 2. Fallback: Direct website contact page scraping
        if not emails:
            scraped = self.scrape_emails_from_website(f"https://{clean_domain}")
            emails.extend(scraped)

        # Deduplicate and clean
        unique_emails = list(dict.fromkeys(e.lower().strip() for e in emails if "@" in e))
        return unique_emails

    def scrape_emails_from_website(self, website_url: str) -> List[str]:
        """
        Scrapes contact emails directly from a website's homepage and contact page.
        """
        if not website_url:
            return []

        target_urls = [website_url]
        clean_base = website_url.rstrip("/")
        target_urls.extend([
            f"{clean_base}/contact",
            f"{clean_base}/contact-us",
            f"{clean_base}/about",
            f"{clean_base}/about-us",
        ])

        found_emails = set()
        email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

        # Ignored non-human or asset extensions
        ignored_extensions = (".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".pdf", ".css", ".js")

        for url in target_urls:
            try:
                resp = self._session.get(url, timeout=5, verify=False)
                if resp.status_code == 200:
                    # Find mailto: links first
                    mailtos = re.findall(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', resp.text, re.IGNORECASE)
                    for m in mailtos:
                        found_emails.add(m.lower())

                    # Regex scan text
                    matches = email_regex.findall(resp.text)
                    for match in matches:
                        match_lower = match.lower()
                        if not any(match_lower.endswith(ext) for ext in ignored_extensions):
                            # Filter out placeholder example emails
                            if not any(dummy in match_lower for dummy in ["example.com", "domain.com", "yoursite.com", "email@"]):
                                found_emails.add(match_lower)

                    if found_emails:
                        break  # Found emails, no need to crawl more pages
            except Exception:
                continue

        return list(found_emails)

    def find_email_for_business(
        self, business_name: str, website: Optional[str]
    ) -> Optional[str]:
        """
        High-level method to discover the primary contact email for a business.
        """
        if not website:
            return None

        emails = self.find_emails_by_domain(website)
        if emails:
            # Prioritize info@, contact@, hello@, sales@, or first available
            for preferred in ["info@", "contact@", "hello@", "support@", "admin@", "sales@"]:
                for e in emails:
                    if e.startswith(preferred):
                        return e
            return emails[0]

        return None

    def find_ceo_or_decision_maker(
        self, business_name: str, city: str = "Dubai", domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Target strictly the CEO / Owner / Founder / Managing Director of a company.
        Bypasses junior staff, managers, and assistants.
        """
        executive_titles = ["CEO", "Chief Executive Officer", "Founder", "Co-Founder", "Owner", "Managing Director", "President", "Partner"]
        forbidden_titles = ["Manager", "Assistant", "Associate", "Sales Rep", "Intern", "Accountant", "Staff", "Clerk"]

        result = {
            "name": None,
            "title": "CEO / Managing Director",
            "email": None,
            "linkedin": None,
            "verified": False,
        }

        # 1. Try Snov.io prospects search by company name if authenticated
        token = self._get_access_token()
        if token:
            try:
                # Snov.io prospect search endpoint
                url = "https://api.snov.io/v1/get-prospects-by-company"
                headers = {"Authorization": f"Bearer {token}"}
                payload = {
                    "company_name": business_name,
                    "positions": ["CEO", "Founder", "Owner", "Managing Director"],
                }
                resp = self._session.post(url, headers=headers, json=payload, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    prospects = data.get("prospects", []) or data.get("data", [])
                    for p in prospects:
                        pos = (p.get("position") or p.get("title") or "").strip()
                        # Strict check: reject managers or assistant
                        if any(f.lower() in pos.lower() for f in forbidden_titles):
                            continue
                        if any(ex.lower() in pos.lower() for ex in executive_titles):
                            first_n = p.get("firstName") or p.get("first_name", "")
                            last_n = p.get("lastName") or p.get("last_name", "")
                            full_n = f"{first_n} {last_n}".strip() or p.get("name")
                            if full_n:
                                result["name"] = full_n
                                result["title"] = pos
                                result["email"] = p.get("email") or (p.get("emails", [None])[0] if isinstance(p.get("emails"), list) else None)
                                result["linkedin"] = p.get("social", {}).get("linkedin") or p.get("linkedin")
                                result["verified"] = True
                                logger.info(f"Discovered CEO for {business_name} via Snov: {full_n} ({pos})")
                                return result
            except Exception as exc:
                logger.debug(f"Snov prospect search error: {exc}")

        # 2. SerpApi LinkedIn Executive Search fallback
        if settings.has_serpapi():
            try:
                query = f'"{business_name}" "{city}" (CEO OR "Managing Director" OR Founder OR Owner) site:linkedin.com/in/'
                params = {
                    "engine": "google",
                    "q": query,
                    "api_key": settings.serpapi_api_key,
                    "num": 3,
                }
                resp = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
                if resp.status_code == 200:
                    res = resp.json()
                    organic = res.get("organic_results", [])
                else:
                    organic = []
                for item in organic:
                    title_str = item.get("title", "")
                    # Example: "Ahmed Al Qasimi - CEO - Al Quoz Trading | LinkedIn"
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")

                    if " - " in title_str:
                        parts = [p.strip() for p in title_str.split("-")]
                        candidate_name = parts[0]
                        candidate_title = parts[1] if len(parts) > 1 else "CEO"
                        # Clean up LinkedIn suffix
                        candidate_title = candidate_title.replace("| LinkedIn", "").replace("LinkedIn", "").strip()

                        if not any(f.lower() in candidate_title.lower() for f in forbidden_titles):
                            result["name"] = candidate_name
                            result["title"] = candidate_title
                            result["linkedin"] = link
                            logger.info(f"Discovered CEO for {business_name} via LinkedIn/Google: {candidate_name} ({candidate_title})")
                            break
            except Exception as exc:
                logger.debug(f"SerpApi executive search failed: {exc}")

        return result


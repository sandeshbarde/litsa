"""
Apollo.io Executive & CEO Discovery Service.
Discovers verified emails and LinkedIn profiles for CEOs, Founders, and Owners.
Bypasses generic staff and junior managers.
"""

from typing import Dict, Any, Optional, List
import requests
from loguru import logger

from app.config import settings


class ApolloService:
    """Service to discover verified CEO / Owner contacts using Apollo.io API."""

    BASE_URL = "https://api.apollo.io/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or getattr(settings, "apollo_api_key", None) or "").strip()

    def is_active(self) -> bool:
        """Check if Apollo API key is configured."""
        return bool(self.api_key and self.api_key != "YOUR_APOLLO_KEY")

    def find_ceo_or_owner(
        self,
        company_name: str,
        domain: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query Apollo.io to find the CEO, Founder, or Owner of the company.
        Strictly filters out managers, associates, and junior employees.
        """
        result = {
            "name": None,
            "title": "CEO / Owner",
            "email": None,
            "linkedin": None,
            "verified": False,
            "source": "apollo",
        }

        if not self.is_active():
            return result

        try:
            url = f"{self.BASE_URL}/mixed_people/search"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": self.api_key,
            }
            payload = {
                "q_organization_name": company_name,
                "person_titles": ["CEO", "Chief Executive Officer", "Founder", "Co-Founder", "Owner", "Managing Director", "President"],
                "page": 1,
                "per_page": 5,
            }
            if domain:
                payload["q_organization_domains"] = [domain]

            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                people = data.get("people", []) or []
                for p in people:
                    title = p.get("title", "")
                    # Reject non-executives
                    if any(bad in title.lower() for bad in ["manager", "assistant", "clerk", "rep", "intern"]):
                        continue

                    full_name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or p.get("name")
                    email = p.get("email")
                    linkedin = p.get("linkedin_url")

                    if full_name or email:
                        result["name"] = full_name or "CEO / Owner"
                        result["title"] = title or "CEO"
                        result["email"] = email
                        result["linkedin"] = linkedin
                        result["verified"] = bool(email and "@" in email)
                        logger.info(f"Apollo found CEO for '{company_name}': {full_name} ({title}) - {email}")
                        return result
            else:
                logger.warning(f"Apollo API returned {resp.status_code}: {resp.text}")

        except Exception as exc:
            logger.error(f"Apollo API request error: {exc}")

        return result


apollo_service = ApolloService()

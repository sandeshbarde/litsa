"""
Apify Google Maps Scraper Service.
Uses Apify Store Actors (e.g. compass/crawler-google-places) to scrape Google Maps leads
worldwide with zero monthly quota blocks, filtering 100% NO-WEBSITE targets.
"""

from typing import List, Dict, Any, Optional
import requests
from loguru import logger

from app.config import settings


class ApifyService:
    """Service to discover businesses using Apify Store Google Maps Scraper actor."""

    BASE_URL = "https://api.apify.com/v2"
    # Official high-volume Google Maps Scraper on Apify Store
    ACTOR_ID = "compass~crawler-google-places"

    def __init__(self, api_token: Optional[str] = None):
        if api_token is not None:
            self.api_token = api_token.strip()
        else:
            self.api_token = (getattr(settings, "apify_api_token", None) or "").strip()

    def is_active(self) -> bool:
        token = self.api_token or ""
        return bool(token and not token.startswith("YOUR_") and len(token) > 20)

    def search_businesses(
        self,
        query: str,
        city: str = "Dubai",
        max_items: int = 25,
        timeout: int = 90,
    ) -> List[Dict[str, Any]]:
        """Alias for scrape_leads providing standard discovery provider interface."""
        return self.scrape_leads(query=query, city=city, max_items=max_items, timeout=timeout)

    def scrape_leads(
        self,
        query: str,
        city: str = "Dubai",
        max_items: int = 25,
        timeout: int = 90,
    ) -> List[Dict[str, Any]]:
        """
        Run Google Maps scraper on Apify Store and extract businesses.
        Strictly filters out any business that already possesses an active website.
        """
        if not self.is_active():
            logger.warning("Apify API token not configured; skipping Apify discovery.")
            return []

        if city.lower() in query.lower() or " in " in query.lower():
            search_string = query
        else:
            search_string = f"{query} in {city}"
        logger.info(f"Starting Apify Google Maps run for: '{search_string}' (max {max_items})")

        actor_url = f"{self.BASE_URL}/acts/{self.ACTOR_ID}/run-sync-get-dataset-items?token={self.api_token}&timeout={timeout}"
        payload = {
            "searchStringsArray": [search_string],
            "maxCrawledPlacesPerSearch": max_items,
            "language": "en",
            "skipClosedPlaces": True,
        }

        try:
            resp = requests.post(actor_url, json=payload, timeout=timeout + 10)
            if resp.status_code in [200, 201]:
                raw_items = resp.json() or []
                logger.info(f"Apify returned {len(raw_items)} raw places for '{search_string}'. Filtering 100% no-website leads...")
                
                filtered_leads = []
                for item in raw_items:
                    website = (item.get("website") or "").strip()
                    # 100% Strict Policy: Discard anyone with an existing website
                    if website and website.startswith("http"):
                        continue

                    title = item.get("title") or item.get("name")
                    if not title:
                        continue

                    lead = {
                        "business_name": title,
                        "category": item.get("categoryName") or item.get("category") or "Commercial Trader",
                        "city": city,
                        "area": item.get("neighborhood") or item.get("city") or city,
                        "address": item.get("address") or item.get("street"),
                        "phone": item.get("phone") or item.get("phoneUnformatted"),
                        "website": None,
                        "website_status": "NO_WEBSITE",
                        "google_rating": item.get("totalScore") or item.get("rating"),
                        "google_review_count": item.get("reviewsCount") or 0,
                        "source": "apify_google_maps",
                    }
                    filtered_leads.append(lead)

                logger.info(f"Apify filtered {len(filtered_leads)} qualified NO-WEBSITE targets.")
                return filtered_leads
            else:
                err_msg = f"Apify HTTP {resp.status_code}: {resp.text[:200]}"
                logger.warning(f"Apify actor call returned error: {err_msg}")
                raise RuntimeError(err_msg)

        except Exception as exc:
            logger.error(f"Apify scrape execution error: {exc}")
            raise exc


apify_service = ApifyService()

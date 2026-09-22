"""
SerpApi Google Maps engine client.
Finds local businesses by area + category in Dubai.
"""

from typing import Optional, List, Dict, Any
from loguru import logger

from app.api.serpapi_base import SerpApiClient
from app.config import settings


class GoogleMapsClient(SerpApiClient):
    """Client for the SerpApi google_maps engine."""

    def __init__(self):
        super().__init__(engine="google_maps")

    def search_businesses(
        self,
        query: str,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search for businesses using Google Maps engine.
        Returns a list of normalized business dicts.
        """
        params = {
            "q": query,
            "type": "search",
            "hl": "en",
            "gl": "ae",  # UAE
        }

        data = self.search(params)
        if not data:
            return []

        raw_results = data.get("local_results", [])
        businesses = []
        for item in raw_results[:max_results]:
            parsed = self._parse_result(item, query)
            if parsed:
                businesses.append(parsed)

        logger.info(f"Maps query '{query}' → {len(businesses)} results.")
        return businesses

    def get_place_details(
        self, data_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch place details using data_id.
        """
        params = {
            "type": "place",
            "data": data_id,
            "hl": "en",
        }
        data = self.search(params)
        if not data:
            return None
        place = data.get("place_results", {})
        return self._parse_place_details(place)

    @staticmethod
    def _parse_result(item: dict, query: str = "") -> Optional[dict]:
        """Parse a single Maps result into a normalized dict."""
        name = item.get("title") or item.get("name")
        if not name:
            return None

        # Extract website - check multiple fields
        website = (
            item.get("website")
            or item.get("domain")
            or None
        )

        # Extract phone
        phone = item.get("phone") or item.get("phone_number") or None

        # GPS coordinates
        gps = item.get("gps_coordinates", {})

        # Hours / open state
        hours = item.get("hours") or item.get("operating_hours") or None
        open_state = item.get("open_state") or None

        return {
            "business_name": name,
            "place_id": item.get("place_id") or None,
            "data_id": item.get("data_id") or None,
            "address": item.get("address") or None,
            "phone": phone,
            "website": website,
            "google_maps_url": item.get("link") or None,
            "google_rating": item.get("rating") or None,
            "google_review_count": item.get("reviews") or item.get("reviews_original") or None,
            "business_status": item.get("type") or None,
            "open_state": open_state,
            "description": item.get("description") or None,
            "booking_link": item.get("reservation_link") or item.get("booking") or None,
            "thumbnail": item.get("thumbnail") or None,
            "latitude": gps.get("latitude") if gps else None,
            "longitude": gps.get("longitude") if gps else None,
            "source": "serpapi_maps",
        }

    @staticmethod
    def _parse_place_details(place: dict) -> Optional[dict]:
        """Parse place_results into a normalized dict."""
        if not place:
            return None
        return {
            "business_name": place.get("title") or place.get("name"),
            "address": place.get("address"),
            "phone": place.get("phone"),
            "website": place.get("website"),
            "google_rating": place.get("rating"),
            "google_review_count": place.get("reviews"),
            "description": place.get("description"),
            "open_state": place.get("open_state"),
            "booking_link": place.get("reservation_link"),
        }

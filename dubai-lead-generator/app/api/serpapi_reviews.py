"""
SerpApi Google Maps Reviews engine client.
Only called when ENABLE_REVIEWS=true.
"""

from typing import Optional, List, Dict, Any
from loguru import logger

from app.api.serpapi_base import SerpApiClient
from app.config import settings


class GoogleMapsReviewsClient(SerpApiClient):
    """Client for the SerpApi google_maps_reviews engine."""

    def __init__(self):
        super().__init__(engine="google_maps_reviews")

    def get_reviews(
        self, data_id: str, max_reviews: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve public reviews for a business.
        Only called when enabled in settings.
        """
        if not settings.enable_reviews:
            logger.debug("Reviews disabled by config. Skipping.")
            return []

        params = {
            "data_id": data_id,
            "hl": "en",
        }
        data = self.search(params)
        if not data:
            return []

        reviews = data.get("reviews", [])[:max_reviews]
        parsed = []
        for r in reviews:
            parsed.append({
                "author": r.get("user", {}).get("name"),
                "rating": r.get("rating"),
                "text": r.get("snippet") or r.get("text"),
                "date": r.get("date") or r.get("iso_date"),
            })
        logger.info(f"Retrieved {len(parsed)} reviews for data_id={data_id}.")
        return parsed

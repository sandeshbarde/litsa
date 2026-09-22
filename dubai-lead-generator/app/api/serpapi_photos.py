"""
SerpApi Google Maps Photos engine client.
Only called when ENABLE_PHOTOS=true.
"""

from typing import Optional, List, Dict, Any
from loguru import logger

from app.api.serpapi_base import SerpApiClient
from app.config import settings


class GoogleMapsPhotosClient(SerpApiClient):
    """Client for the SerpApi google_maps_photos engine."""

    def __init__(self):
        super().__init__(engine="google_maps_photos")

    def get_photos(
        self, data_id: str, max_photos: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve public photo metadata for a business.
        Only called when enabled in settings.
        """
        if not settings.enable_photos:
            logger.debug("Photos disabled by config. Skipping.")
            return []

        params = {
            "data_id": data_id,
            "hl": "en",
        }
        data = self.search(params)
        if not data:
            return []

        photos = data.get("photos", [])[:max_photos]
        parsed = [
            {
                "url": p.get("photo") or p.get("url"),
                "title": p.get("title"),
                "category": p.get("category"),
            }
            for p in photos
        ]
        logger.info(f"Retrieved {len(parsed)} photos for data_id={data_id}.")
        return parsed

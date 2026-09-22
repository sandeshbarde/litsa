"""
Social presence discovery service.
Uses Google Search to find public Instagram/Facebook pages.
"""

from typing import Dict, Optional
from loguru import logger

from app.config import settings


class SocialCheckService:
    """Finds public social media pages for a business."""

    def __init__(self, google_client=None):
        self._google = google_client

    def find_social(
        self, business_name: str, area: str
    ) -> Dict[str, Optional[str]]:
        """
        Returns {instagram_url, facebook_url, other_social_url}.
        Does NOT attempt login or access private data.
        """
        empty = {"instagram_url": None, "facebook_url": None, "other_social_url": None}
        if not self._google:
            return empty
        if not settings.has_serpapi():
            logger.debug("SerpApi not configured; skipping social check.")
            return empty

        try:
            result = self._google.find_social_pages(business_name, area)
            return result
        except Exception as exc:
            logger.warning(f"Social check failed for '{business_name}': {exc}")
            return empty

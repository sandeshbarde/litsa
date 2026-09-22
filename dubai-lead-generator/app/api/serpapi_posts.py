"""
SerpApi Google Maps Posts engine client.
Only called when ENABLE_POSTS=true.
"""

from typing import Optional, List, Dict, Any
from loguru import logger

from app.api.serpapi_base import SerpApiClient
from app.config import settings


class GoogleMapsPostsClient(SerpApiClient):
    """Client for the SerpApi google_maps_posts engine."""

    def __init__(self):
        super().__init__(engine="google_maps_posts")

    def get_posts(
        self, data_id: str, max_posts: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve public Google Maps posts for a business.
        Only called when enabled in settings.
        """
        if not settings.enable_posts:
            logger.debug("Posts disabled by config. Skipping.")
            return []

        params = {
            "data_id": data_id,
            "hl": "en",
        }
        data = self.search(params)
        if not data:
            return []

        posts = data.get("posts", [])[:max_posts]
        parsed = [
            {
                "title": p.get("title"),
                "summary": p.get("summary") or p.get("snippet"),
                "published_date": p.get("published_date") or p.get("date"),
                "link": p.get("link"),
            }
            for p in posts
        ]
        logger.info(f"Retrieved {len(parsed)} posts for data_id={data_id}.")
        return parsed

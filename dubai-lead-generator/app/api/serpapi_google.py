"""
SerpApi Google Search engine client.
Used for website verification and social presence discovery.
"""

from typing import Optional, List, Dict, Any
from loguru import logger

from app.api.serpapi_base import SerpApiClient


class GoogleSearchClient(SerpApiClient):
    """Client for the SerpApi google engine."""

    def __init__(self):
        super().__init__(engine="google")

    def search(
        self,
        query: str,
        num: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """Run a Google search and return raw results."""
        params = {
            "q": query,
            "num": num,
            "hl": "en",
            "gl": "ae",
        }
        return super().search(params)

    def get_organic_results(
        self, query: str, num: int = 10
    ) -> List[Dict[str, Any]]:
        """Return list of organic search results."""
        data = self.search(query, num=num)
        if not data:
            return []
        return data.get("organic_results", [])

    def find_website(
        self, business_name: str, area: str
    ) -> Optional[str]:
        """
        Try to find an official website for a business via Google Search.
        Returns the first non-social, non-directory URL found.
        """
        from app.utils.normalization import is_social_only_domain, is_directory_domain

        query = f'"{business_name}" "{area}" Dubai official website'
        results = self.get_organic_results(query, num=5)
        for result in results:
            link = result.get("link") or ""
            if link and not is_social_only_domain(link) and not is_directory_domain(link):
                logger.debug(f"Google found website for '{business_name}': {link}")
                return link

        # Fallback: broader search
        query2 = f'"{business_name}" Dubai'
        results2 = self.get_organic_results(query2, num=5)
        for result in results2:
            link = result.get("link") or ""
            if link and not is_social_only_domain(link) and not is_directory_domain(link):
                return link

        return None

    def find_social_pages(
        self, business_name: str, area: str
    ) -> Dict[str, Optional[str]]:
        """
        Search for Instagram and Facebook pages for a business.
        Returns dict with instagram_url, facebook_url, other_social_url.
        """
        social = {"instagram_url": None, "facebook_url": None, "other_social_url": None}
        query = f'"{business_name}" Dubai site:instagram.com OR site:facebook.com'
        results = self.get_organic_results(query, num=5)
        for result in results:
            link = result.get("link") or ""
            if not link:
                continue
            if "instagram.com" in link and not social["instagram_url"]:
                social["instagram_url"] = link
            elif "facebook.com" in link and not social["facebook_url"]:
                social["facebook_url"] = link
            elif social["other_social_url"] is None:
                if any(s in link for s in ["twitter.com", "x.com", "tiktok.com", "linkedin.com"]):
                    social["other_social_url"] = link

        logger.debug(
            f"Social for '{business_name}': IG={social['instagram_url']}, "
            f"FB={social['facebook_url']}"
        )
        return social

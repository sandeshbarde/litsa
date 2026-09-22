"""
Provider abstraction and resilient fallback engine for B2B Lead Discovery.
Supports SerpApi Google Maps and Apify Google Maps Scraper with exponential backoff,
quota/rate-limit awareness, credit estimation, and automatic failover.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import time
import requests
from loguru import logger

from app.config import settings


class LeadDiscoveryProvider(ABC):
    """Abstract base class defining the provider contract for lead collection."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if required credentials are present."""
        pass

    @abstractmethod
    def search_businesses(
        self,
        query: str,
        google_gl: str = "ae",
        google_hl: str = "en",
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Search businesses for the specified query.
        Returns: (list_of_raw_lead_dicts, telemetry_metadata)
        """
        pass


class SerpApiProvider(LeadDiscoveryProvider):
    """SerpApi Google Maps engine implementation."""

    @property
    def name(self) -> str:
        return "serpapi_maps"

    def is_configured(self) -> bool:
        return settings.has_serpapi()

    def search_businesses(
        self,
        query: str,
        google_gl: str = "ae",
        google_hl: str = "en",
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        start_time = time.time()
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_maps",
            "q": query,
            "gl": google_gl,
            "hl": google_hl,
            "api_key": settings.serpapi_api_key,
        }

        retries = 2
        last_error = None
        for attempt in range(retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=20)
                latency = round(time.time() - start_time, 2)

                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("local_results", [])
                    meta = {
                        "provider": self.name,
                        "success": True,
                        "latency_seconds": latency,
                        "results_count": len(results),
                        "estimated_credits": 1,
                        "retries": attempt,
                    }
                    return results, meta

                if resp.status_code == 429 or "run out of searches" in resp.text.lower():
                    meta = {
                        "provider": self.name,
                        "success": False,
                        "quota_exhausted": True,
                        "status_code": resp.status_code,
                        "latency_seconds": latency,
                        "error": "Quota exhausted or rate limit hit.",
                    }
                    return [], meta

                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as exc:
                last_error = str(exc)

            if attempt < retries:
                time.sleep(2 ** attempt)

        latency = round(time.time() - start_time, 2)
        return [], {
            "provider": self.name,
            "success": False,
            "latency_seconds": latency,
            "error": last_error,
        }


class ApifyProvider(LeadDiscoveryProvider):
    """Apify Google Maps scraper actor implementation."""

    @property
    def name(self) -> str:
        return "apify_maps"

    def is_configured(self) -> bool:
        return settings.has_apify()

    def search_businesses(
        self,
        query: str,
        google_gl: str = "ae",
        google_hl: str = "en",
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        start_time = time.time()
        from app.services.apify_service import apify_service

        if not apify_service.is_active():
            return [], {"provider": self.name, "success": False, "error": "Apify token not active"}

        try:
            results = apify_service.search_businesses(query=query, max_items=limit)
            latency = round(time.time() - start_time, 2)

            # Normalize Apify output to match standard engine format
            normalized_results = []
            for r in results:
                b_name = r.get("business_name") or r.get("title") or r.get("name")
                b_rating = r.get("google_rating") or r.get("totalScore") or r.get("rating")
                b_reviews = r.get("google_review_count") or r.get("reviewsCount") or r.get("reviews") or 0
                normalized_results.append({
                    "business_name": b_name,
                    "title": b_name,
                    "place_id": r.get("place_id") or r.get("placeId"),
                    "data_id": r.get("data_id") or r.get("dataId") or r.get("cid"),
                    "type": r.get("category") or r.get("categoryName"),
                    "address": r.get("address") or r.get("street"),
                    "phone": r.get("phone") or r.get("phoneUnformatted"),
                    "website": r.get("website"),
                    "rating": b_rating,
                    "reviews": b_reviews,
                    "google_rating": b_rating,
                    "google_review_count": b_reviews,
                    "link": r.get("link") or r.get("url"),
                    "description": r.get("description"),
                })

            meta = {
                "provider": self.name,
                "success": True,
                "latency_seconds": latency,
                "results_count": len(normalized_results),
                "estimated_credits": max(1, len(normalized_results) // 10),
            }
            return normalized_results, meta
        except Exception as exc:
            latency = round(time.time() - start_time, 2)
            return [], {
                "provider": self.name,
                "success": False,
                "latency_seconds": latency,
                "error": str(exc),
            }


class ResilientDiscoveryEngine:
    """Orchestrates primary and fallback discovery providers."""

    def __init__(self):
        self.providers: List[LeadDiscoveryProvider] = []
        if settings.has_apify():
            self.providers.append(ApifyProvider())
        if settings.has_serpapi():
            self.providers.append(SerpApiProvider())

    def search_with_failover(
        self,
        query: str,
        google_gl: str = "ae",
        google_hl: str = "en",
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes query on primary provider, falling back on error or quota exhaustion.
        """
        if not self.providers:
            return [], {"provider": "none", "success": False, "error": "No discovery provider configured"}

        telemetry_trail = []
        for provider in self.providers:
            if not provider.is_configured():
                continue

            results, meta = provider.search_businesses(
                query=query, google_gl=google_gl, google_hl=google_hl, limit=limit
            )
            telemetry_trail.append(meta)

            if meta.get("success") and results:
                meta["failover_history"] = telemetry_trail
                return results, meta

            logger.warning(
                f"Provider '{provider.name}' failed or returned 0 results for query '{query}': {meta.get('error')}. Attempting next provider..."
            )

        return [], {
            "provider": "failed_all",
            "success": False,
            "failover_history": telemetry_trail,
            "error": "All discovery providers failed or returned zero results.",
        }


# Singleton engine instance
discovery_engine = ResilientDiscoveryEngine()

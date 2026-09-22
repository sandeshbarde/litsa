"""
Base SerpApi client with rate limiting, retry, and quota detection.
"""

import time
import random
from typing import Optional, Dict, Any

import requests
from loguru import logger

from app.config import settings
from app.utils.retry import APIQuotaError, APIAuthError

SERPAPI_BASE_URL = "https://serpapi.com/search"
DEFAULT_TIMEOUT = 30


class SerpApiClient:
    """Base client for all SerpApi engines."""

    def __init__(self, engine: str):
        self.engine = engine
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    def search(
        self,
        params: Dict[str, Any],
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
    ) -> Optional[Dict[str, Any]]:
        """Execute a SerpApi search with retry and quota handling."""
        if not settings.has_serpapi():
            logger.warning("SERPAPI_API_KEY not configured. Skipping API call.")
            return None

        full_params = {
            "engine": self.engine,
            "api_key": settings.serpapi_api_key,
            **params,
        }

        attempt = 0
        while attempt < max_retries:
            attempt += 1
            try:
                logger.debug(f"SerpApi [{self.engine}] attempt {attempt}: {self._safe_params(params)}")
                response = self._session.get(
                    SERPAPI_BASE_URL,
                    params=full_params,
                    timeout=timeout,
                )

                if response.status_code == 429:
                    wait = min(5 * (2 ** (attempt - 1)), 60)
                    logger.warning(f"SerpApi rate limit hit. Waiting {wait}s before retry.")
                    time.sleep(wait)
                    continue

                if response.status_code in (401, 403):
                    raise APIAuthError(
                        f"SerpApi auth error {response.status_code}: check SERPAPI_API_KEY"
                    )

                response.raise_for_status()
                data = response.json()

                # Detect quota exhaustion in response body
                if self._is_quota_error(data):
                    raise APIQuotaError("SerpApi quota exhausted.")

                logger.debug(f"SerpApi [{self.engine}] success.")
                return data

            except (APIQuotaError, APIAuthError):
                raise
            except requests.exceptions.Timeout:
                logger.warning(f"SerpApi [{self.engine}] timeout (attempt {attempt}).")
                if attempt >= max_retries:
                    logger.error(f"SerpApi [{self.engine}] exhausted retries on timeout.")
                    return None
                time.sleep(2 ** attempt + random.uniform(0, 1))
            except requests.exceptions.RequestException as exc:
                logger.warning(f"SerpApi [{self.engine}] request error: {exc} (attempt {attempt}).")
                if attempt >= max_retries:
                    logger.error(f"SerpApi [{self.engine}] exhausted retries.")
                    return None
                time.sleep(2 ** attempt + random.uniform(0, 1))

        return None

    @staticmethod
    def _safe_params(params: dict) -> dict:
        """Return params dict with sensitive keys redacted."""
        return {
            k: "[REDACTED]" if k in ("api_key",) else v
            for k, v in params.items()
        }

    @staticmethod
    def _is_quota_error(data: dict) -> bool:
        error_msg = (data.get("error") or "").lower()
        return any(kw in error_msg for kw in ["credit", "limit", "quota", "exhausted"])

"""
Retry utilities with exponential backoff.
Uses tenacity for robust retry logic.
"""

import time
import random
from functools import wraps
from typing import Callable, Type, Tuple, Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)
from loguru import logger
import requests


# Standard retry for HTTP requests
def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (requests.exceptions.RequestException,),
):
    """Decorator factory for retrying functions with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exc = None
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    attempt += 1
                    last_exc = exc
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {exc}"
                        )
                        raise
                    wait = min(min_wait * (2 ** (attempt - 1)) + random.uniform(0, 1), max_wait)
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {exc}. "
                        f"Retrying in {wait:.1f}s..."
                    )
                    time.sleep(wait)
            raise last_exc

        return wrapper

    return decorator


def is_rate_limit_error(exc: Exception) -> bool:
    """Detect rate limit / quota errors."""
    if isinstance(exc, requests.exceptions.HTTPError):
        if exc.response is not None and exc.response.status_code == 429:
            return True
    msg = str(exc).lower()
    return any(kw in msg for kw in ["quota", "rate limit", "too many requests", "429"])


def is_auth_error(exc: Exception) -> bool:
    """Detect authentication / authorization errors (do not retry)."""
    if isinstance(exc, requests.exceptions.HTTPError):
        if exc.response is not None and exc.response.status_code in (401, 403):
            return True
    return False


class APIQuotaError(Exception):
    """Raised when an API quota is exhausted."""
    pass


class APIAuthError(Exception):
    """Raised when API authentication fails."""
    pass

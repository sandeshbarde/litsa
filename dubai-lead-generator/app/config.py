"""
Central configuration loader.
Loads settings from environment variables (.env) and config.yaml.
NEVER logs or exposes secret values.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Model configuration for Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys (never logged)
    serpapi_api_key: str = Field(default="")
    gemini_api_key: str = Field(default="")
    snov_user_id: str = Field(default="")
    snov_secret: str = Field(default="")
    google_sheet_id: str = Field(default="")
    google_service_account_json: str = Field(
        default="credentials/service_account.json"
    )

    # Database
    database_url: str = Field(default="sqlite:///./dubai_leads.db")

    # SMTP & Email Dispatch (optional)
    smtp_host: Optional[str] = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_username: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    resend_api_key: Optional[str] = Field(default=None)
    zerobounce_api_key: Optional[str] = Field(default=None)
    apollo_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    apify_api_token: Optional[str] = Field(default=None)

    # Feature flags
    free_mode: bool = Field(default=True)
    enable_reviews: bool = Field(default=False)
    enable_photos: bool = Field(default=False)
    enable_posts: bool = Field(default=False)
    enable_gemini: bool = Field(default=False)
    enable_zerobounce: bool = Field(default=True)
    enable_web_verification: bool = Field(default=True)

    # Limits
    max_businesses_per_query: int = Field(default=20)
    max_total_businesses_per_run: int = Field(default=100)
    max_web_verification_calls: int = Field(default=100)

    # App Environment & Public URLs
    app_env: str = Field(default="development")  # development, staging, production
    public_base_url: str = Field(default="http://127.0.0.1:8000")
    frontend_origin: str = Field(default="http://127.0.0.1:8000")

    # Security & Admin Authentication
    admin_email: str = Field(default="admin@litsa.io")
    admin_password_hash: str = Field(default="")
    admin_default_password: str = Field(default="Admin@Litsa2026!")
    jwt_secret: str = Field(default="litsa-super-secret-production-jwt-key-2026")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=1440)

    # Redis & Celery
    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/0")

    # AI Model Central Config
    gemini_model: str = Field(default="gemini-2.5-flash")

    # Email Sender Defaults
    email_from_name: str = Field(default="Sandesh Barde")
    email_from_address: str = Field(default="onboarding@resend.dev")
    reply_to: str = Field(default="sandywebx1@gmail.com")

    # Quota & Safe Testing
    stop_at_quota_percent: float = Field(default=80.0)
    provider_test_mode: bool = Field(default=False)
    test_recipient_email: Optional[str] = Field(default=None)

    # App
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    debug: bool = Field(default=False)
    secret_key: str = Field(default="change-me-in-production")

    def has_serpapi(self) -> bool:
        return bool(self.serpapi_api_key and self.serpapi_api_key != "YOUR_SERPAPI_KEY")

    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key != "YOUR_GEMINI_API_KEY")

    def has_sheets(self) -> bool:
        return bool(
            self.google_sheet_id
            and self.google_sheet_id != "YOUR_GOOGLE_SHEET_ID"
            and Path(self.google_service_account_json).exists()
        )

    def has_snov(self) -> bool:
        return bool(self.snov_user_id and self.snov_secret)

    def has_zerobounce(self) -> bool:
        return bool(self.zerobounce_api_key and self.zerobounce_api_key.strip())

    def has_apollo(self) -> bool:
        return bool(self.apollo_api_key and self.apollo_api_key.strip())

    def has_anthropic(self) -> bool:
        return bool(
            self.anthropic_api_key
            and self.anthropic_api_key.strip()
            and not self.anthropic_api_key.startswith("YOUR_")
            and "..." not in self.anthropic_api_key
        )

    def has_apify(self) -> bool:
        return bool(
            self.apify_api_token
            and self.apify_api_token.strip()
            and not self.apify_api_token.startswith("YOUR_")
        )

    def safe_repr(self) -> dict:
        """Return config without secrets for logging."""
        return {
            "free_mode": self.free_mode,
            "enable_reviews": self.enable_reviews,
            "enable_photos": self.enable_photos,
            "enable_posts": self.enable_posts,
            "enable_gemini": self.enable_gemini,
            "enable_web_verification": self.enable_web_verification,
            "max_businesses_per_query": self.max_businesses_per_query,
            "max_total_businesses_per_run": self.max_total_businesses_per_run,
            "max_web_verification_calls": self.max_web_verification_calls,
            "has_serpapi": self.has_serpapi(),
            "has_apify": self.has_apify(),
            "has_gemini": self.has_gemini(),
            "has_anthropic": self.has_anthropic(),
            "has_snov": self.has_snov(),
            "has_sheets": self.has_sheets(),
        }


class YamlConfig:
    """Runtime configuration from config.yaml."""

    def __init__(self, path: str = "config.yaml"):
        self._path = Path(path)
        self._data: dict = {}
        self.load()

    def load(self) -> None:
        if self._path.exists():
            with open(self._path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
        else:
            self._data = {}

    def save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True)

    @property
    def areas(self) -> List[str]:
        return self._data.get("areas", [])

    @areas.setter
    def areas(self, value: List[str]) -> None:
        self._data["areas"] = value

    @property
    def global_cities(self) -> list:
        return self._data.get("global_cities", [])

    @property
    def categories(self) -> List[str]:
        return self._data.get("categories", [])

    @categories.setter
    def categories(self, value: List[str]) -> None:
        self._data["categories"] = value

    @property
    def lead_scoring(self) -> dict:
        return self._data.get("lead_scoring", {})

    @property
    def website_check(self) -> dict:
        return self._data.get("website_check", {})

    @property
    def sheets_config(self) -> dict:
        return self._data.get("sheets", {})

    @property
    def scheduler_config(self) -> dict:
        return self._data.get("scheduler", {})

    @property
    def logging_config(self) -> dict:
        return self._data.get("logging", {})

    def get(self, key: str, default=None):
        return self._data.get(key, default)


# Singletons
settings = Settings()
yaml_config = YamlConfig()


def build_demo_url(lead_id: str) -> str:
    """Build a public recipient-facing demo URL using PUBLIC_BASE_URL."""
    base = (settings.public_base_url or "").strip().rstrip("/")
    if not base:
        base = "http://127.0.0.1:8000"
    return f"{base}/demo/{lead_id}"

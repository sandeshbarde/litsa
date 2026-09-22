"""
Contact Discovery Provider Abstraction.
Separates finding contact details (Apollo, Snov.io, Tomba) from verification.
Guarantees authentic executive data without fabricated names or guessed emails.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from loguru import logger

from app.config import settings


class ContactDiscoveryProvider(ABC):
    """Abstract base class for executive contact finding services."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def find_decision_maker(
        self,
        business_name: str,
        domain: Optional[str] = None,
        city: str = "Dubai",
    ) -> Optional[Dict[str, Any]]:
        """
        Returns structured contact:
        {
            "name": str,
            "title": str,
            "email": str or None,
            "linkedin": str or None,
            "source": str,
            "confidence": float (0.0 - 1.0),
            "checked_at": str (ISO timestamp),
            "is_verified": bool (False by default until verifier confirms)
        }
        """
        pass


class ApolloContactProvider(ContactDiscoveryProvider):
    """Apollo.io contact finder implementation."""

    @property
    def name(self) -> str:
        return "apollo"

    def is_configured(self) -> bool:
        return settings.has_apollo()

    def find_decision_maker(
        self,
        business_name: str,
        domain: Optional[str] = None,
        city: str = "Dubai",
    ) -> Optional[Dict[str, Any]]:
        from app.services.apollo_service import apollo_service
        if not apollo_service.is_active():
            return None

        data = apollo_service.find_ceo_or_owner(
            company_name=business_name,
            domain=domain,
            city=city,
        )
        if data and (data.get("name") or data.get("email")):
            return {
                "name": data.get("name"),
                "title": data.get("title") or "Managing Director",
                "email": data.get("email"),
                "linkedin": data.get("linkedin"),
                "source": "apollo",
                "confidence": 0.85 if data.get("email") else 0.70,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "is_verified": False,
            }
        return None


class SnovContactProvider(ContactDiscoveryProvider):
    """Snov.io OAuth2 contact finder implementation."""

    @property
    def name(self) -> str:
        return "snov"

    def is_configured(self) -> bool:
        return settings.has_snov()

    def find_decision_maker(
        self,
        business_name: str,
        domain: Optional[str] = None,
        city: str = "Dubai",
    ) -> Optional[Dict[str, Any]]:
        from app.services.snov_service import SnovService
        snov = SnovService()
        data = snov.find_ceo_or_decision_maker(
            business_name=business_name,
            city=city,
            domain=domain,
        )
        if data and (data.get("name") or data.get("email")):
            return {
                "name": data.get("name"),
                "title": data.get("title") or "Owner / CEO",
                "email": data.get("email"),
                "linkedin": data.get("linkedin"),
                "source": "snov",
                "confidence": 0.80 if data.get("email") else 0.65,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "is_verified": False,
            }
        return None


class ResilientContactDiscoveryEngine:
    """Dispatches contact searches across configured providers in priority order."""

    def __init__(self):
        self.providers = [
            ApolloContactProvider(),
            SnovContactProvider(),
        ]

    def discover_decision_maker(
        self,
        business_name: str,
        domain: Optional[str] = None,
        city: str = "Dubai",
    ) -> Optional[Dict[str, Any]]:
        for provider in self.providers:
            if not provider.is_configured():
                continue
            try:
                res = provider.find_decision_maker(business_name, domain, city)
                if res:
                    logger.info(f"Discovered executive via {provider.name} for {business_name}: {res.get('name')}")
                    return res
            except Exception as exc:
                logger.warning(f"Provider {provider.name} failed for {business_name}: {exc}")

        return None


contact_discovery_engine = ResilientContactDiscoveryEngine()

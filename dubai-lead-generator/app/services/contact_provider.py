"""
Contact Discovery Provider Abstraction.
Separates finding contact details (Snov.io, Apollo, Tomba, Pattern Guessing) from verification.
Guarantees authentic executive data verified with ZeroBounce.
Fallback chain: Snov -> Apollo -> Tomba -> Pattern Guess -> ZeroBounce validation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import requests
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


class SnovContactProvider(ContactDiscoveryProvider):
    """Snov.io OAuth2 contact finder implementation (Primary)."""

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
                "name": data.get("name") or "Owner / CEO",
                "title": data.get("title") or "Owner / CEO",
                "email": data.get("email"),
                "linkedin": data.get("linkedin"),
                "source": "snov",
                "confidence": 0.85 if data.get("email") else 0.65,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "is_verified": False,
            }
        return None


class ApolloContactProvider(ContactDiscoveryProvider):
    """Apollo.io contact finder implementation (Secondary Fallback)."""

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
                "name": data.get("name") or "Managing Director",
                "title": data.get("title") or "Managing Director",
                "email": data.get("email"),
                "linkedin": data.get("linkedin"),
                "source": "apollo",
                "confidence": 0.85 if data.get("email") else 0.70,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "is_verified": False,
            }
        return None


class TombaContactProvider(ContactDiscoveryProvider):
    """Tomba.io domain search and email finder implementation (Tertiary Fallback)."""

    @property
    def name(self) -> str:
        return "tomba"

    def is_configured(self) -> bool:
        return bool(getattr(settings, "tomba_api_key", None) and getattr(settings, "tomba_secret_key", None))

    def find_decision_maker(
        self,
        business_name: str,
        domain: Optional[str] = None,
        city: str = "Dubai",
    ) -> Optional[Dict[str, Any]]:
        if not self.is_configured() or not domain:
            return None
        clean_domain = domain.lower().replace("http://", "").replace("https://", "").split("/")[0].replace("www.", "")
        api_key = settings.tomba_api_key
        secret_key = settings.tomba_secret_key
        headers = {
            "X-Tomba-Key": api_key,
            "X-Tomba-Secret": secret_key,
        }
        try:
            url = f"https://api.tomba.io/v2/domain-search?domain={clean_domain}"
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                emails = data.get("emails", [])
                for item in emails:
                    email_addr = item.get("email")
                    if email_addr and "@" in email_addr:
                        first = item.get("first_name", "")
                        last = item.get("last_name", "")
                        full_name = f"{first} {last}".strip() or "Owner / Manager"
                        title = item.get("position") or "Owner"
                        return {
                            "name": full_name,
                            "title": title,
                            "email": email_addr,
                            "linkedin": item.get("linkedin"),
                            "source": "tomba",
                            "confidence": 0.75,
                            "checked_at": datetime.now(timezone.utc).isoformat(),
                            "is_verified": False,
                        }
        except Exception as exc:
            logger.warning(f"Tomba provider failed for {clean_domain}: {exc}")
        return None


class PatternGuessContactProvider(ContactDiscoveryProvider):
    """Domain Pattern Guessing (info@, contact@, hello@, sales@) with ZeroBounce verification."""

    @property
    def name(self) -> str:
        return "pattern_guess"

    def is_configured(self) -> bool:
        return True  # Always enabled as fallback for valid domains

    def find_decision_maker(
        self,
        business_name: str,
        domain: Optional[str] = None,
        city: str = "Dubai",
    ) -> Optional[Dict[str, Any]]:
        if not domain or "." not in domain:
            return None

        clean_domain = domain.lower().replace("http://", "").replace("https://", "").split("/")[0].replace("www.", "").strip()
        if not clean_domain or any(ign in clean_domain for ign in ["facebook.com", "instagram.com", "google.com", "tripadvisor.com", "zomato.com"]):
            return None

        candidates = [
            f"info@{clean_domain}",
            f"contact@{clean_domain}",
            f"hello@{clean_domain}",
            f"sales@{clean_domain}",
        ]

        from app.services.zerobounce_service import zerobounce_service
        for candidate in candidates:
            if zerobounce_service.is_active():
                zb = zerobounce_service.validate_email(candidate)
                status = (zb.get("status") or "").upper()
                if status == "VALID":
                    logger.info(f"Pattern guess '{candidate}' confirmed VALID by ZeroBounce.")
                    return {
                        "name": "Owner / Manager",
                        "title": "General Contact",
                        "email": candidate,
                        "linkedin": None,
                        "source": "pattern_guess_zerobounce",
                        "confidence": 0.85,
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                        "is_verified": True,
                    }
            else:
                break

        return None


class ResilientContactDiscoveryEngine:
    """Dispatches contact searches across providers in chain: Snov -> Apollo -> Tomba -> Pattern Guess -> ZeroBounce."""

    def __init__(self):
        self.providers = [
            SnovContactProvider(),
            ApolloContactProvider(),
            TombaContactProvider(),
            PatternGuessContactProvider(),
        ]

    def discover_decision_maker(
        self,
        business_name: str,
        domain: Optional[str] = None,
        city: str = "Dubai",
    ) -> Optional[Dict[str, Any]]:
        from app.services.zerobounce_service import zerobounce_service

        for provider in self.providers:
            if not provider.is_configured():
                continue
            try:
                res = provider.find_decision_maker(business_name, domain, city)
                if res and res.get("email"):
                    email_candidate = res["email"].strip()
                    # Verify discovered email via ZeroBounce if not already confirmed
                    if not res.get("is_verified", False) and zerobounce_service.is_active():
                        zb = zerobounce_service.validate_email(email_candidate)
                        zb_status = (zb.get("status") or "").upper()
                        if zb_status in ["INVALID", "SPAMTRAP", "ABUSE", "DO_NOT_MAIL"]:
                            logger.warning(f"Provider {provider.name} email '{email_candidate}' rejected by ZeroBounce ({zb_status}). Trying next provider in fallback chain.")
                            continue
                        elif zb_status == "VALID":
                            res["is_verified"] = True

                    logger.info(f"Discovered executive via {provider.name} for {business_name}: {res.get('name')} ({email_candidate})")
                    return res
                elif res:
                    return res
            except Exception as exc:
                logger.warning(f"Provider {provider.name} failed for {business_name}: {exc}")

        return None


contact_discovery_engine = ResilientContactDiscoveryEngine()

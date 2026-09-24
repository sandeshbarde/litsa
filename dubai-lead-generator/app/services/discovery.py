"""
Discovery service: orchestrates area × category job execution.
Manages the full pipeline: search → normalize → dedup → verify → score → save.
"""

import uuid
import time
from datetime import datetime
from typing import List, Optional, Dict, Any

from loguru import logger
from sqlalchemy.orm import Session

from app.config import settings, yaml_config
from app.api.serpapi_maps import GoogleMapsClient
from app.api.serpapi_google import GoogleSearchClient
from app.api.serpapi_reviews import GoogleMapsReviewsClient
from app.api.serpapi_photos import GoogleMapsPhotosClient
from app.api.serpapi_posts import GoogleMapsPostsClient
from app.services.deduplication import DeduplicationService
from app.services.verification import VerificationService
from app.services.social_check import SocialCheckService
from app.services.lead_scoring import LeadScoringService
from app.services.gemini_service import GeminiService
from app.services.loophole_service import loophole_service
from app.services.discovery_provider import discovery_engine
from app.services.location_config import get_location_meta
from app.database import repositories as repo
from app.utils.normalization import (
    normalize_business_name,
    normalize_phone,
    normalize_address,
)

# Global job state registry (in-memory, per process)
_JOB_STATES: Dict[str, str] = {}  # job_id → "running"|"paused"|"cancelled"


def get_job_state(job_id: str) -> str:
    return _JOB_STATES.get(job_id, "running")


def set_job_state(job_id: str, state: str) -> None:
    _JOB_STATES[job_id] = state


class DiscoveryService:
    """Orchestrates the full business discovery and qualification pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.maps_client = GoogleMapsClient()
        self.google_client = GoogleSearchClient()
        self.reviews_client = GoogleMapsReviewsClient()
        self.photos_client = GoogleMapsPhotosClient()
        self.posts_client = GoogleMapsPostsClient()
        self.dedup = DeduplicationService()
        self.verifier = VerificationService()
        self.social = SocialCheckService(google_client=self.google_client)
        self.scorer = LeadScoringService()
        self.gemini = GeminiService()

    def _preload_dedup(self) -> None:
        """Load existing records into dedup service."""
        from sqlalchemy import text
        place_ids = [
            r[0] for r in self.db.execute(text("SELECT place_id FROM businesses WHERE place_id IS NOT NULL")).fetchall()
        ]
        data_ids = [
            r[0] for r in self.db.execute(text("SELECT data_id FROM businesses WHERE data_id IS NOT NULL")).fetchall()
        ]
        phones = repo.get_all_phone_normalized(self.db)
        name_pairs = repo.get_all_name_area_pairs(self.db)
        self.dedup.load_from_db(place_ids, data_ids, phones, name_pairs)

    def generate_queries(
        self,
        areas: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        city: str = "Dubai",
        country: str = "United Arab Emirates",
    ) -> List[Dict[str, str]]:
        """Generate area × category query combinations for any city, state, or country worldwide."""
        categories = categories or yaml_config.categories

        loc_meta = get_location_meta(city, fallback_country=country)
        effective_city = loc_meta.city
        effective_state = loc_meta.state or ""
        effective_country = loc_meta.country

        # Determine effective areas
        clean_areas = [a.strip() for a in (areas or []) if a and a.strip()]
        if not clean_areas:
            if loc_meta.suggested_areas:
                effective_areas = loc_meta.suggested_areas
            else:
                effective_areas = [effective_city]
        else:
            effective_areas = clean_areas

        queries = []
        for area in effective_areas:
            for cat in categories:
                if area == effective_city or not area or area.lower() in ["all", effective_city.lower(), effective_country.lower()]:
                    if effective_state and effective_state != effective_city:
                        query = f"{cat} in {effective_city}, {effective_state}, {effective_country}".strip()
                    else:
                        query = f"{cat} in {effective_city}, {effective_country}".strip()
                    assigned_area = ""
                else:
                    if effective_state and effective_state != effective_city:
                        query = f"{cat} in {area}, {effective_city}, {effective_state}".strip()
                    else:
                        query = f"{cat} in {area}, {effective_city}".strip()
                    assigned_area = area

                queries.append({
                    "area": assigned_area,
                    "category": cat,
                    "city": effective_city,
                    "state": effective_state,
                    "country": effective_country,
                    "query": query
                })
        logger.info(f"Generated {len(queries)} search queries for {effective_city} ({effective_country}).")
        return queries

    def start_run(
        self,
        run_id: str,
        areas: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        max_businesses: Optional[int] = None,
        city: str = "Dubai",
        country: str = "United Arab Emirates",
    ) -> Dict[str, Any]:
        """
        Execute a full discovery run.
        Returns a summary dict.
        """
        max_businesses = max_businesses or settings.max_total_businesses_per_run
        self._preload_dedup()

        queries = self.generate_queries(areas, categories, city=city, country=country)
        total_found = 0
        total_new = 0
        total_duplicates = 0
        job_ids = []
        errors = []

        for q_info in queries:
            if total_new >= max_businesses:
                logger.info(f"Max businesses limit ({max_businesses}) reached. Stopping.")
                break

            # Create job record
            job = repo.create_job(self.db, {
                "id": str(uuid.uuid4()),
                "area": q_info["area"],
                "category": q_info["category"],
                "query": q_info["query"],
                "status": "running",
                "started_at": datetime.utcnow(),
                "parent_run_id": run_id,
            })
            job_ids.append(job.id)
            set_job_state(job.id, "running")

            try:
                results = self._execute_query(
                    job_id=job.id,
                    q_info=q_info,
                    max_businesses=max_businesses - total_new,
                )
                total_found += results["found"]
                total_new += results["new"]
                total_duplicates += results["duplicates"]

                repo.update_job(self.db, job.id, {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "results_found": results["found"],
                })
            except Exception as exc:
                error_msg = str(exc)
                errors.append(error_msg)
                logger.error(f"Job {job.id} failed: {error_msg}")
                repo.update_job(self.db, job.id, {
                    "status": "failed",
                    "completed_at": datetime.utcnow(),
                    "errors": error_msg,
                })

            # Small delay between queries to respect rate limits
            time.sleep(1.0)

        summary = {
            "run_id": run_id,
            "city": city,
            "queries_executed": len(job_ids),
            "total_found": total_found,
            "total_new": total_new,
            "total_duplicates": total_duplicates,
            "errors": len(errors),
            "job_ids": job_ids,
        }
        logger.info(f"Run {run_id} complete: {summary}")
        return summary

    def _execute_query(
        self,
        job_id: str,
        q_info: Dict[str, str],
        max_businesses: int,
    ) -> Dict[str, int]:
        """Execute a single area × category query and process results."""
        area = q_info["area"]
        category = q_info["category"]
        query = q_info["query"]
        city = q_info.get("city", "Dubai")
        country = q_info.get("country", "United Arab Emirates")

        logger.info(f"[{job_id}] Searching: '{query}' ({city}, {country})")

        loc_meta = get_location_meta(city, fallback_country=country)
        raw_businesses, telemetry = discovery_engine.search_with_failover(
            query=query,
            google_gl=loc_meta.google_gl,
            google_hl=loc_meta.default_language,
            limit=settings.max_businesses_per_query,
        )

        found = len(raw_businesses)
        new_count = 0
        dup_count = 0

        for raw in raw_businesses:
            # Check job state (pause/cancel support)
            state = get_job_state(job_id)
            if state == "cancelled":
                logger.info(f"Job {job_id} cancelled.")
                break
            while state == "paused":
                logger.debug(f"Job {job_id} paused. Waiting...")
                time.sleep(2)
                state = get_job_state(job_id)

            if new_count >= max_businesses:
                break

            biz = self._process_business(raw, area, category, city=city, country=country)
            if biz is None:
                dup_count += 1
            else:
                new_count += 1

        return {"found": found, "new": new_count, "duplicates": dup_count}

    def _process_business(
        self, raw: dict, area: str, category: str, city: str = "Dubai", country: str = "United Arab Emirates"
    ):
        """Process a single raw business result through the full pipeline."""
        name = raw.get("business_name") or raw.get("title") or raw.get("name")
        if not name:
            return None

        place_id = raw.get("place_id")
        data_id = raw.get("data_id")
        phone = raw.get("phone")

        logger.info(f"[STAGE 1: DISCOVERY] Processing business candidate '{name}' in {area} ({city})")

        # Dedup check
        is_dup, reason = self.dedup.is_duplicate(
            place_id=place_id,
            data_id=data_id,
            phone=phone,
            business_name=name,
            area=area,
        )
        if is_dup:
            logger.debug(f"[STAGE 1: DISCOVERY] Duplicate detected: '{name}' ({reason})")
            return None

        # Normalize
        phone_norm = normalize_phone(phone)
        name_norm = normalize_business_name(name)
        address = raw.get("address")
        address_norm = normalize_address(address)

        # Stage 2: Website verification
        logger.info(f"[STAGE 2: VERIFICATION] Verifying web presence for '{name}'...")
        website = raw.get("website")
        use_google_verify = settings.enable_web_verification and not settings.free_mode
        website_status, verified_url, http_code = self.verifier.verify(
            website=website,
            business_name=name,
            area=area,
            google_search_client=self.google_client if use_google_verify else None,
        )

        # STRICT NO-WEBSITE FILTER
        if website_status == "WEBSITE_WORKING" or (verified_url and website_status not in ["NO_WEBSITE", "WEBSITE_DOWN", "UNREACHABLE", "SOCIAL_ONLY"]):
            logger.info(f"[STAGE 2: VERIFICATION] Strict Filter: Skipping '{name}' - has working website ({verified_url or website}).")
            return None

        # Social presence
        if not settings.free_mode:
            social_info = self.social.find_social(name, area)
        else:
            social_info = {"instagram_url": None, "facebook_url": None, "other_social_url": None}
        has_social = bool(
            social_info.get("instagram_url") or social_info.get("facebook_url")
        )

        # Optional: reviews
        reviews = []
        if settings.enable_reviews and data_id:
            reviews = self.reviews_client.get_reviews(data_id)

        # Lead scoring
        review_count = raw.get("google_review_count") or 0
        has_phone = bool(phone_norm)
        has_booking = bool(raw.get("booking_link"))
        has_description = bool(raw.get("description"))

        score, breakdown, priority = self.scorer.compute_score(
            website_status=website_status,
            review_count=int(review_count) if review_count else 0,
            has_phone=has_phone,
            has_social=has_social,
            has_booking=has_booking,
            has_description=has_description,
        )

        # Stage 3: Loophole Research & Company Profiling
        logger.info(f"[STAGE 3: LOOPHOLE PROFILING] Analyzing revenue leak for '{name}'...")
        loophole_info = loophole_service.analyze_company_and_loophole(
            business_name=name,
            category=category,
            city=city,
            area=area,
            google_rating=raw.get("google_rating"),
            review_count=int(review_count) if review_count else None,
            description=raw.get("description"),
        )

        # Optional Gemini classification
        website_quality = None
        if settings.enable_gemini:
            gemini_result = self.gemini.analyze_lead(
                business_name=name,
                category=category,
                area=area,
                website_status=website_status,
                review_count=int(review_count) if review_count else None,
                has_social=has_social,
                description=raw.get("description"),
            )
            if gemini_result:
                website_quality = gemini_result.get("website_quality")

        # Stage 4: Executive Contact Discovery & Email Guesser Fallback
        logger.info(f"[STAGE 4: CONTACT DISCOVERY] Finding executive contact for '{name}'...")
        from app.services.contact_provider import contact_discovery_engine
        from app.services.email_guesser import email_guesser
        from app.utils.normalization import extract_domain

        extracted_domain = extract_domain(verified_url or website)
        discovered_contact = contact_discovery_engine.discover_decision_maker(
            business_name=name,
            domain=extracted_domain,
            city=city,
        )

        email_found = None
        decision_maker_name = None
        decision_maker_title = None
        contact_channel_val = "email"

        if discovered_contact and discovered_contact.get("email"):
            email_found = discovered_contact.get("email")
            decision_maker_name = discovered_contact.get("name")
            decision_maker_title = discovered_contact.get("title")
            contact_status_val = "discovered"
            contact_channel_val = "email"
        elif raw.get("email"):
            email_found = raw.get("email")
            contact_status_val = "discovered"
            contact_channel_val = "email"
        else:
            # Fallback 3: Direct SMTP Email Guesser & Phone Channel Routing
            guessed_email, channel, guess_meta = email_guesser.discover_contact(
                business_name=name,
                website=verified_url or website,
                phone=phone,
            )
            if guessed_email:
                email_found = guessed_email
                contact_status_val = "discovered"
                contact_channel_val = "email"
            else:
                contact_status_val = "manual_research_needed"
                contact_channel_val = channel

        loc_meta = get_location_meta(city, fallback_country=country)

        # Save to DB
        biz_data = {
            "id": str(uuid.uuid4()),
            "place_id": place_id,
            "data_id": data_id,
            "business_name": name,
            "business_name_normalized": name_norm,
            "category": category,
            "city": loc_meta.city,
            "state": loc_meta.state or "",
            "country": loc_meta.country,
            "business_type": loophole_info.get("business_type", "B2B"),
            "is_dealer_or_wholesale": loophole_info.get("is_dealer_or_wholesale", False),
            "area": area,
            "address": address,
            "address_normalized": address_norm,
            "phone": phone,
            "phone_normalized": phone_norm,
            "email": email_found,
            "contact_channel": contact_channel_val,
            "decision_maker_name": decision_maker_name,
            "decision_maker_title": decision_maker_title,
            "decision_maker_email": email_found,
            "contact_status": contact_status_val,
            "website": website,
            "website_status": website_status,
            "website_url_verified": verified_url,
            "website_quality": website_quality,
            "loophole_summary": loophole_info.get("primary_loophole"),
            "loophole_data": loophole_info,
            "google_maps_url": raw.get("google_maps_url"),
            "google_rating": raw.get("google_rating"),
            "google_review_count": int(review_count) if review_count else None,
            "instagram_url": social_info.get("instagram_url"),
            "facebook_url": social_info.get("facebook_url"),
            "other_social_url": social_info.get("other_social_url"),
            "business_status": raw.get("business_status"),
            "open_state": raw.get("open_state"),
            "description": raw.get("description"),
            "booking_link": raw.get("booking_link"),
            "has_booking": has_booking,
            "lead_score": score,
            "lead_priority": priority,
            "score_breakdown": breakdown,
            "sequence_stage": "NOT_STARTED",
            "source": raw.get("source", "serpapi_maps"),
            "first_seen": datetime.utcnow(),
            "last_checked": datetime.utcnow(),
        }

        business = repo.create_business(self.db, biz_data)

        # Register in dedup
        self.dedup.register(
            place_id=place_id,
            data_id=data_id,
            phone=phone_norm,
            business_name=name,
            area=area,
        )

        logger.info(
            f"Saved: '{name}' | {area} | Score={score} ({priority}) | "
            f"Website={website_status}"
        )
        return business

    def verify_single(
        self, business_id: str
    ) -> Optional[Dict[str, Any]]:
        """Re-verify website and social for a single business."""
        business = repo.get_business(self.db, business_id)
        if not business:
            return None

        website_status, verified_url, http_code = self.verifier.verify(
            website=business.website,
            business_name=business.business_name,
            area=business.area or "",
            google_search_client=self.google_client,
        )

        social_info = self.social.find_social(
            business.business_name, business.area or ""
        )
        has_social = bool(
            social_info.get("instagram_url") or social_info.get("facebook_url")
        )

        score, breakdown, priority = self.scorer.compute_score(
            website_status=website_status,
            review_count=business.google_review_count or 0,
            has_phone=bool(business.phone_normalized),
            has_social=has_social,
            has_booking=bool(business.booking_link),
            has_description=bool(business.description),
        )

        updates = {
            "website_status": website_status,
            "website_url_verified": verified_url,
            "instagram_url": social_info.get("instagram_url") or business.instagram_url,
            "facebook_url": social_info.get("facebook_url") or business.facebook_url,
            "lead_score": score,
            "lead_priority": priority,
            "score_breakdown": breakdown,
            "last_checked": datetime.utcnow(),
        }

        repo.update_business(self.db, business_id, updates)

        # Record verification
        repo.create_verification(self.db, {
            "business_id": business_id,
            "url_checked": verified_url,
            "http_status_code": http_code,
            "resolved": website_status == "WEBSITE_WORKING",
            "website_status": website_status,
        })

        return {**updates, "business_id": business_id}

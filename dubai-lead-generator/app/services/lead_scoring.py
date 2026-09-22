"""
Transparent lead scoring service.
Scores are deterministic, documented, and stored as JSON breakdown.
"""

from typing import Dict, Any, Tuple
from app.config import yaml_config


class LeadScoringService:
    """Computes a lead score with a visible breakdown."""

    def __init__(self):
        cfg = yaml_config.lead_scoring
        self.weights = {
            "no_website": cfg.get("no_website", 40),
            "active_social": cfg.get("active_social", 15),
            "reviews_100_plus": cfg.get("reviews_100_plus", 15),
            "reviews_50_99": cfg.get("reviews_50_99", 10),
            "phone_available": cfg.get("phone_available", 10),
            "no_booking_flow": cfg.get("no_booking_flow", 10),
            "good_public_info": cfg.get("good_public_info", 5),
        }
        thresholds = cfg.get("thresholds", {})
        self.hot_threshold = thresholds.get("hot", 70)
        self.warm_threshold = thresholds.get("warm", 45)

    def compute_score(
        self,
        website_status: str,
        review_count: int,
        has_phone: bool,
        has_social: bool,
        has_booking: bool,
        has_description: bool,
    ) -> Tuple[int, Dict[str, Any], str]:
        """
        Returns (score, breakdown_dict, priority).
        """
        breakdown: Dict[str, int] = {}
        score = 0

        # No verified website
        if website_status in ("NO_WEBSITE", "SOCIAL_ONLY", "DIRECTORY_ONLY", "WEBSITE_BROKEN"):
            breakdown["no_website"] = self.weights["no_website"]
            score += self.weights["no_website"]

        # Active social presence
        if has_social:
            breakdown["active_social"] = self.weights["active_social"]
            score += self.weights["active_social"]

        # Review count tiers
        if review_count and review_count >= 100:
            breakdown["reviews_100_plus"] = self.weights["reviews_100_plus"]
            score += self.weights["reviews_100_plus"]
        elif review_count and review_count >= 50:
            breakdown["reviews_50_99"] = self.weights["reviews_50_99"]
            score += self.weights["reviews_50_99"]

        # Phone available
        if has_phone:
            breakdown["phone_available"] = self.weights["phone_available"]
            score += self.weights["phone_available"]

        # No booking/contact flow
        if not has_booking:
            breakdown["no_booking_flow"] = self.weights["no_booking_flow"]
            score += self.weights["no_booking_flow"]

        # Good public information
        if has_description:
            breakdown["good_public_info"] = self.weights["good_public_info"]
            score += self.weights["good_public_info"]

        # Cap at 100
        score = min(score, 100)

        # Priority
        if score >= self.hot_threshold:
            priority = "HOT"
        elif score >= self.warm_threshold:
            priority = "WARM"
        else:
            priority = "LOW"

        return score, breakdown, priority

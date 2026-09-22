"""
Unit tests for lead scoring.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patch yaml_config to use default values
from unittest.mock import patch, MagicMock

mock_yaml = MagicMock()
mock_yaml.lead_scoring = {
    "no_website": 40,
    "active_social": 15,
    "reviews_100_plus": 15,
    "reviews_50_99": 10,
    "phone_available": 10,
    "no_booking_flow": 10,
    "good_public_info": 5,
    "thresholds": {"hot": 70, "warm": 45},
}

with patch("app.config.yaml_config", mock_yaml):
    from app.services.lead_scoring import LeadScoringService


def make_scorer():
    with patch("app.services.lead_scoring.yaml_config", mock_yaml):
        return LeadScoringService()


def test_hot_lead_no_website():
    scorer = make_scorer()
    score, breakdown, priority = scorer.compute_score(
        website_status="NO_WEBSITE",
        review_count=120,
        has_phone=True,
        has_social=True,
        has_booking=False,
        has_description=True,
    )
    assert score >= 70
    assert priority == "HOT"
    assert "no_website" in breakdown
    assert "reviews_100_plus" in breakdown


def test_warm_lead():
    scorer = make_scorer()
    score, breakdown, priority = scorer.compute_score(
        website_status="NO_WEBSITE",
        review_count=30,
        has_phone=True,
        has_social=False,
        has_booking=False,
        has_description=False,
    )
    assert 45 <= score < 70
    assert priority == "WARM"


def test_low_lead_with_working_website():
    scorer = make_scorer()
    score, breakdown, priority = scorer.compute_score(
        website_status="WEBSITE_WORKING",
        review_count=5,
        has_phone=False,
        has_social=False,
        has_booking=True,
        has_description=False,
    )
    assert score < 45
    assert priority == "LOW"


def test_score_capped_at_100():
    scorer = make_scorer()
    score, breakdown, priority = scorer.compute_score(
        website_status="NO_WEBSITE",
        review_count=200,
        has_phone=True,
        has_social=True,
        has_booking=False,
        has_description=True,
    )
    assert score <= 100


def test_breakdown_transparency():
    scorer = make_scorer()
    _, breakdown, _ = scorer.compute_score(
        website_status="SOCIAL_ONLY",
        review_count=75,
        has_phone=True,
        has_social=True,
        has_booking=True,
        has_description=False,
    )
    assert isinstance(breakdown, dict)
    assert all(isinstance(v, int) for v in breakdown.values())

"""
Tests for Loophole Research, CEO Pitch Generator, and Strict No-Website Filtering.
"""

import pytest
from app.services.loophole_service import loophole_service
from app.services.pitch_generator import pitch_generator


def test_b2b_wholesale_loophole_classification():
    data = loophole_service.analyze_company_and_loophole(
        business_name="Al Quoz Building Materials Trading LLC",
        category="building materials wholesale",
        city="Dubai",
        area="Al Quoz Industrial",
        google_rating=4.7,
        review_count=85,
    )
    assert data["business_type"] == "B2B"
    assert data["is_dealer_or_wholesale"] is True
    assert "Catalog" in data["primary_loophole"] or "B2B" in data["primary_loophole"]
    assert "lost" in data["estimated_revenue_leak"].lower() or "estimated" in data["estimated_revenue_leak"].lower()


def test_b2c_service_loophole_classification():
    data = loophole_service.analyze_company_and_loophole(
        business_name="Golden Scissors Luxury Salon",
        category="salons",
        city="Dubai",
        area="Jumeirah",
        google_rating=4.9,
        review_count=120,
    )
    assert data["business_type"] == "B2C"
    assert "Booking" in data["primary_loophole"] or "Google" in data["primary_loophole"]


def test_ceo_pitch_generator_step_1():
    loophole_data = loophole_service.analyze_company_and_loophole(
        business_name="Emirates Heavy Machinery Spare Parts",
        category="auto spare parts wholesale",
        city="Dubai",
    )
    pitch = pitch_generator.generate_ceo_pitch(
        business_name="Emirates Heavy Machinery Spare Parts",
        category="auto spare parts wholesale",
        city="Dubai",
        ceo_name="Tariq Mansoor",
        ceo_title="Managing Director",
        loophole_data=loophole_data,
        sequence_step=1,
    )
    assert "Tariq Mansoor" in pitch["body"]
    assert "Loophole" in pitch["body"]
    assert "custom personal website" in pitch["body"].lower()
    assert "Emirates Heavy Machinery Spare Parts" in pitch["subject"]


def test_ceo_pitch_generator_step_2_and_3():
    loophole_data = loophole_service.analyze_company_and_loophole(
        business_name="Gulf Steel Distributors",
        category="industrial equipment suppliers",
        city="Riyadh",
    )
    # Step 2: Follow-up
    pitch_2 = pitch_generator.generate_ceo_pitch(
        business_name="Gulf Steel Distributors",
        category="industrial equipment suppliers",
        city="Riyadh",
        ceo_name="Fahad Al Otaibi",
        loophole_data=loophole_data,
        sequence_step=2,
    )
    assert "Following up" in pitch_2["body"]
    assert "Riyadh" in pitch_2["subject"]

    # Step 3: Demo preview
    pitch_3 = pitch_generator.generate_ceo_pitch(
        business_name="Gulf Steel Distributors",
        category="industrial equipment suppliers",
        city="Riyadh",
        ceo_name="Fahad Al Otaibi",
        loophole_data=loophole_data,
        sequence_step=3,
    )
    assert "Interactive Prototype" in pitch_3["body"]
    assert pitch_3["mockup_url"].startswith("https://preview")


def test_website_mockup_generation():
    mockup = pitch_generator.generate_website_mockup_data(
        business_name="Apex Global Chemical Supplies",
        category="chemicals wholesale",
        city="London",
        phone="+44 20 7946 0991",
        loophole_data={"business_type": "B2B", "industry": "Industrial Supplies"}
    )
    assert mockup["business_name"] == "Apex Global Chemical Supplies"
    assert "Wholesale" in mockup["hero_title"] or "Commercial" in mockup["hero_title"]
    assert len(mockup["services"]) == 3
    assert mockup["accent_color"] == "#4f46e5"

"""
Seed script: populates the SQLite database with realistic Dubai sample leads.
Allows testing the dashboard, search, filters, scoring, and pitch generation
even before configuring a SerpApi key.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db import SessionLocal, init_db
from app.models import Business, SearchJob
from app.utils.normalization import normalize_business_name, normalize_phone, normalize_address


SAMPLE_LEADS = [
    {
        "business_name": "Al Safadi Grill & Cafe",
        "category": "Restaurant",
        "area": "Downtown Dubai",
        "address": "Sheikh Mohammed bin Rashid Blvd, Downtown Dubai",
        "phone": "+971 4 345 6789",
        "website": None,
        "website_status": "NO_WEBSITE",
        "google_rating": 4.6,
        "google_review_count": 182,
        "google_maps_url": "https://maps.google.com/?q=Al+Safadi+Grill+Dubai",
        "instagram_url": "https://instagram.com/alsafadigrill",
        "lead_score": 85,
        "lead_priority": "HOT",
        "score_breakdown": {"no_website": 40, "high_rating": 25, "active_social": 20},
        "description": "Authentic Lebanese charcoal grill and cafe in downtown Dubai.",
    },
    {
        "business_name": "Marina Elite Real Estate",
        "category": "Real Estate",
        "area": "Dubai Marina",
        "address": "Marina Gate Tower 1, Dubai Marina",
        "phone": "+971 4 876 5432",
        "website": "http://marinaelitedxb.com",
        "website_status": "WEBSITE_BROKEN",
        "google_rating": 4.8,
        "google_review_count": 94,
        "google_maps_url": "https://maps.google.com/?q=Marina+Elite+Real+Estate",
        "instagram_url": "https://instagram.com/marinaeliterealty",
        "lead_score": 75,
        "lead_priority": "HOT",
        "score_breakdown": {"broken_website": 35, "high_rating": 25, "commercial_value": 15},
        "description": "Luxury waterfront property specialists in Dubai Marina and JBR.",
    },
    {
        "business_name": "Desert Rose Beauty Lounge",
        "category": "Salon",
        "area": "Business Bay",
        "address": "Executive Towers B, Business Bay, Dubai",
        "phone": "+971 4 234 5678",
        "website": None,
        "website_status": "NO_WEBSITE",
        "google_rating": 4.5,
        "google_review_count": 68,
        "google_maps_url": "https://maps.google.com/?q=Desert+Rose+Beauty+Lounge",
        "instagram_url": "https://instagram.com/desertrosedxb",
        "lead_score": 70,
        "lead_priority": "WARM",
        "score_breakdown": {"no_website": 40, "medium_reviews": 15, "active_social": 15},
        "description": "Premium ladies salon and spa offering hair, nail, and skincare treatments.",
    },
    {
        "business_name": "Apex Management Consulting",
        "category": "Consulting",
        "area": "Business Bay",
        "address": "The Binary Tower, Business Bay, Dubai",
        "phone": "+971 4 555 1212",
        "website": "https://apexconsulting.ae",
        "website_status": "WEBSITE_WORKING",
        "google_rating": 4.2,
        "google_review_count": 22,
        "google_maps_url": "https://maps.google.com/?q=Apex+Management+Consulting",
        "instagram_url": None,
        "lead_score": 25,
        "lead_priority": "LOW",
        "score_breakdown": {"website_working": -30, "moderate_rating": 15},
        "description": "Corporate restructuring, tax advisory, and mainland business setup.",
    },
    {
        "business_name": "Al Quoz Artisan Auto Garage",
        "category": "Automotive",
        "area": "Al Quoz",
        "address": "Street 18, Al Quoz Industrial 3, Dubai",
        "phone": "+971 4 999 8877",
        "website": None,
        "website_status": "NO_WEBSITE",
        "google_rating": 4.7,
        "google_review_count": 140,
        "google_maps_url": "https://maps.google.com/?q=Al+Quoz+Artisan+Auto",
        "instagram_url": None,
        "lead_score": 80,
        "lead_priority": "HOT",
        "score_breakdown": {"no_website": 40, "high_rating": 25, "high_reviews": 15},
        "description": "Specialist European car repair, tuning, and denting/painting in Al Quoz.",
    },
    {
        "business_name": "Deira Spice Oasis Restaurant",
        "category": "Restaurant",
        "area": "Deira",
        "address": "Al Rigga Road, Deira, Dubai",
        "phone": "+971 4 222 3344",
        "website": None,
        "website_status": "NO_WEBSITE",
        "google_rating": 4.4,
        "google_review_count": 210,
        "google_maps_url": "https://maps.google.com/?q=Deira+Spice+Oasis",
        "instagram_url": "https://instagram.com/deiraspiceoasis",
        "lead_score": 85,
        "lead_priority": "HOT",
        "score_breakdown": {"no_website": 40, "high_reviews": 25, "active_social": 20},
        "description": "Traditional Mandi, Biryani, and Arabian seafood specialties in Deira.",
    },
    {
        "business_name": "Palm Fitness & Personal Training",
        "category": "Fitness",
        "area": "Palm Jumeirah",
        "address": "Golden Mile Galleria, Palm Jumeirah, Dubai",
        "phone": "+971 4 444 8899",
        "website": "http://palmfitnessdubai.org/broken",
        "website_status": "WEBSITE_BROKEN",
        "google_rating": 4.9,
        "google_review_count": 88,
        "google_maps_url": "https://maps.google.com/?q=Palm+Fitness+Dubai",
        "instagram_url": "https://instagram.com/palmfitdxb",
        "lead_score": 75,
        "lead_priority": "HOT",
        "score_breakdown": {"broken_website": 35, "high_rating": 25, "active_social": 15},
        "description": "Boutique personal training studio and nutritional coaching on the Palm.",
    },
    {
        "business_name": "Jumeirah Dental & Aesthetics",
        "category": "Healthcare",
        "area": "Jumeirah",
        "address": "Jumeirah Beach Road, Jumeirah 1, Dubai",
        "phone": "+971 4 333 1122",
        "website": "https://jumeirahdentalclinic.com",
        "website_status": "WEBSITE_WORKING",
        "google_rating": 4.6,
        "google_review_count": 56,
        "google_maps_url": "https://maps.google.com/?q=Jumeirah+Dental+Aesthetics",
        "instagram_url": "https://instagram.com/jumeirahdental",
        "lead_score": 30,
        "lead_priority": "LOW",
        "score_breakdown": {"website_working": -30, "aesthetic_niche": 20},
        "description": "Cosmetic dentistry, smile makeovers, and orthodontic care in Jumeirah.",
    },
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Business).count()
        print(f"Current business count in database: {existing}")

        # Add SearchJob record
        sample_job = SearchJob(
            id=str(uuid.uuid4()),
            area="Business Bay",
            category="Restaurant",
            query="Restaurant in Business Bay Dubai",
            status="completed",
            started_at=datetime.utcnow() - timedelta(minutes=15),
            completed_at=datetime.utcnow() - timedelta(minutes=10),
            results_found=len(SAMPLE_LEADS),
        )
        db.add(sample_job)

        inserted = 0
        for data in SAMPLE_LEADS:
            norm_name = normalize_business_name(data["business_name"])
            norm_phone = normalize_phone(data["phone"])
            norm_addr = normalize_address(data["address"])

            # Check if business already exists
            found = db.query(Business).filter(
                Business.business_name == data["business_name"]
            ).first()
            if not found:
                biz = Business(
                    id=str(uuid.uuid4()),
                    business_name=data["business_name"],
                    business_name_normalized=norm_name,
                    category=data["category"],
                    area=data["area"],
                    address=data["address"],
                    address_normalized=norm_addr,
                    phone=data["phone"],
                    phone_normalized=norm_phone,
                    website=data["website"],
                    website_status=data["website_status"],
                    google_rating=data["google_rating"],
                    google_review_count=data["google_review_count"],
                    google_maps_url=data["google_maps_url"],
                    instagram_url=data["instagram_url"],
                    lead_score=data["lead_score"],
                    lead_priority=data["lead_priority"],
                    score_breakdown=data["score_breakdown"],
                    description=data["description"],
                    source="seed_sample",
                    first_seen=datetime.utcnow(),
                    last_checked=datetime.utcnow(),
                )
                db.add(biz)
                inserted += 1

        db.commit()
        print(f"Successfully seeded {inserted} sample Dubai leads!")
        print(f"Total businesses now in database: {db.query(Business).count()}")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

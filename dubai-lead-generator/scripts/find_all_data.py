"""
Live Data Discovery Runner.
Searches live Dubai businesses via SerpApi across key areas and categories,
verifies their websites, computes lead scores, and saves them to the database.
"""

import sys
import os
import uuid

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db import SessionLocal, init_db
from app.services.discovery import DiscoveryService
from app.models import Business, SearchJob


def main():
    print("=" * 70)
    print("DUBAI LEAD GENERATOR - FINDING LIVE DATA FROM GOOGLE MAPS")
    print("=" * 70)

    init_db()
    db = SessionLocal()

    try:
        # Target high-value Dubai areas and categories
        areas = ["Business Bay", "Downtown Dubai", "Deira", "Dubai Marina", "Al Quoz"]
        categories = ["salons", "restaurants", "car garages", "real estate agencies"]

        print(f"Target Areas: {areas}")
        print(f"Target Categories: {categories}")
        print("Starting discovery pipeline...")

        service = DiscoveryService(db)
        run_id = str(uuid.uuid4())

        # Fetch up to 40 real businesses across these queries
        summary = service.start_run(
            run_id=run_id,
            areas=areas,
            categories=categories,
            max_businesses=40,
        )

        print("\n" + "=" * 70)
        print("DISCOVERY SUMMARY")
        print("=" * 70)
        print(f"  Queries Executed : {summary['queries_executed']}")
        print(f"  Businesses Found : {summary['total_found']}")
        print(f"  New Leads Saved  : {summary['total_new']}")
        print(f"  Duplicates       : {summary['total_duplicates']}")
        print(f"  Errors           : {summary['errors']}")

        total_in_db = db.query(Business).count()
        hot_leads = db.query(Business).filter(Business.lead_priority == "HOT").count()
        warm_leads = db.query(Business).filter(Business.lead_priority == "WARM").count()
        low_leads = db.query(Business).filter(Business.lead_priority == "LOW").count()
        no_web = db.query(Business).filter(Business.website_status == "NO_WEBSITE").count()

        print("\n" + "=" * 70)
        print("DATABASE TOTALS")
        print("=" * 70)
        print(f"  Total Businesses in DB : {total_in_db}")
        print(f"  HOT Leads              : {hot_leads}")
        print(f"  WARM Leads             : {warm_leads}")
        print(f"  LOW Leads              : {low_leads}")
        print(f"  Businesses with No Web : {no_web}")

        # Print some sample newly found businesses
        print("\nSample Newly Found Dubai Leads:")
        print("-" * 70)
        recent = db.query(Business).order_by(Business.first_seen.desc()).limit(10).all()
        for b in recent:
            print(f"[{b.lead_priority}] {b.business_name} | {b.category} | {b.area}")
            print(f"    Phone: {b.phone or 'N/A'} | Status: {b.website_status} | Web: {b.website or 'NONE'}")
            print(f"    Score: {b.lead_score}/100")

    finally:
        db.close()

    print("\n" + "=" * 70)
    print("SUCCESS: Live data fetched, verified, scored, and ready in dashboard!")
    print("=" * 70)


if __name__ == "__main__":
    main()

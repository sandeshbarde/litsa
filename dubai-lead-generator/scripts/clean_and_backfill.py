"""
Clean and backfill database:
1. Remove all records that have an active website (strictly enforce NO-WEBSITE policy).
2. For all remaining leads, run Loophole Research & Company Profiling.
"""

import sqlite3
import json
from app.services.loophole_service import loophole_service

def clean_and_backfill():
    conn = sqlite3.connect('dubai_leads.db')
    cursor = conn.cursor()

    # 1. Delete all businesses with working websites
    cursor.execute("""
        DELETE FROM businesses 
        WHERE website_status = 'WEBSITE_WORKING' 
           OR (website IS NOT NULL AND website != '' AND website_status NOT IN ('NO_WEBSITE', 'WEBSITE_DOWN', 'UNREACHABLE', 'SOCIAL_ONLY', 'WEBSITE_BROKEN'))
    """)
    deleted_count = cursor.rowcount
    print(f"Purged {deleted_count} businesses with existing websites.")

    # 2. Get all remaining businesses to backfill loophole data
    cursor.execute("""
        SELECT id, business_name, category, area, google_rating, google_review_count, description, city
        FROM businesses
    """)
    rows = cursor.fetchall()
    print(f"Backfilling loophole intelligence for {len(rows)} verified NO-WEBSITE leads...")

    updated = 0
    for row in rows:
        b_id, name, cat, area, rating, review_count, desc, city = row
        city_val = city or "Dubai"

        loophole_info = loophole_service.analyze_company_and_loophole(
            business_name=name,
            category=cat or "Business",
            city=city_val,
            area=area,
            google_rating=rating,
            review_count=review_count,
            description=desc,
        )

        cursor.execute("""
            UPDATE businesses
            SET business_type = ?,
                is_dealer_or_wholesale = ?,
                loophole_summary = ?,
                loophole_data = ?,
                city = ?,
                country = ?,
                sequence_stage = COALESCE(sequence_stage, 'NOT_STARTED')
            WHERE id = ?
        """, (
            loophole_info.get("business_type", "B2B"),
            1 if loophole_info.get("is_dealer_or_wholesale") else 0,
            loophole_info.get("primary_loophole"),
            json.dumps(loophole_info),
            city_val,
            "United Arab Emirates",
            b_id
        ))
        updated += 1

    conn.commit()
    conn.close()
    print(f"Successfully backfilled {updated} leads with deep loophole analysis!")

if __name__ == '__main__':
    clean_and_backfill()

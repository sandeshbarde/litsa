"""
Standalone Google Sheets sync script.
Run this directly to push all DB leads to the configured Google Sheet.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.database.db import init_db, SessionLocal
from app.database.repositories import get_businesses_for_sheet_sync
from app.services.sheets_service import GoogleSheetsService
from app.config import settings


def main():
    print("=" * 60)
    print("Dubai Lead Generator - Google Sheets Sync")
    print("=" * 60)

    if not settings.has_sheets():
        print("ERROR: Google Sheets not configured.")
        print("Check GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON in .env")
        sys.exit(1)

    init_db()
    db = SessionLocal()

    try:
        businesses = get_businesses_for_sheet_sync(db)
        print(f"Found {len(businesses)} businesses to sync.")

        if not businesses:
            print("No businesses found. Run a discovery job first.")
            sys.exit(0)

        sheets = GoogleSheetsService()
        result = sheets.sync_businesses(businesses)

        if result["success"]:
            print(f"Sync complete. {result['synced']} rows written.")
        else:
            print(f"Sync failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    finally:
        db.close()

    print("=" * 60)
    print("Done.")


if __name__ == "__main__":
    main()

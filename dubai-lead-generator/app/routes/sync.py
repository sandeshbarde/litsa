"""
Google Sheets sync endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.repositories import get_businesses_for_sheet_sync
from app.services.sheets_service import GoogleSheetsService

router = APIRouter(prefix="/sync", tags=["sync"])
_sheets_service = GoogleSheetsService()


@router.post("/google-sheets")
def sync_to_google_sheets(
    mode: str = "full",
    db: Session = Depends(get_db),
):
    """
    Sync all leads to Google Sheets.
    mode='full' clears and rewrites all rows.
    mode='append' adds new rows only.
    """
    businesses = get_businesses_for_sheet_sync(db)
    if mode == "append":
        result = _sheets_service.append_businesses(businesses)
    else:
        result = _sheets_service.sync_businesses(businesses)

    return {
        "mode": mode,
        "total_businesses": len(businesses),
        **result,
    }

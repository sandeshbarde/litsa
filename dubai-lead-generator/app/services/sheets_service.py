"""
Google Sheets integration service.
Writes lead data in batch. Never writes credentials to Sheets.
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from loguru import logger

from app.config import settings, yaml_config
from app.models import Business

SHEET_COLUMNS = [
    "ID",
    "Business Name",
    "Category",
    "Area",
    "Address",
    "Phone",
    "Google Maps URL",
    "Website",
    "Website Status",
    "Website Quality",
    "Instagram",
    "Facebook",
    "Google Rating",
    "Review Count",
    "Booking Link",
    "Lead Score",
    "Lead Priority",
    "Score Breakdown",
    "Place ID",
    "Data ID",
    "Business Status",
    "First Seen",
    "Last Checked",
    "Contacted",
    "Contact Date",
    "Contact Status",
    "Follow-up Date",
    "Notes",
    "Source",
]


class GoogleSheetsService:
    """Handles read/write operations to Google Sheets."""

    def __init__(self):
        self._service = None
        self._spreadsheet_id = settings.google_sheet_id
        self._sheet_name = yaml_config.sheets_config.get("worksheet_name", "Leads")
        self._batch_size = yaml_config.sheets_config.get("batch_size", 50)
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Lazy initialization of Google Sheets API client."""
        if self._initialized:
            return self._service is not None

        self._initialized = True
        if not settings.has_sheets():
            logger.warning(
                "Google Sheets not configured. Check GOOGLE_SHEET_ID and "
                "GOOGLE_SERVICE_ACCOUNT_JSON."
            )
            return False

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            creds_path = Path(settings.google_service_account_json)
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
            ]
            creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
            self._service = build("sheets", "v4", credentials=creds)
            logger.info("Google Sheets service initialized.")
            return True
        except Exception as exc:
            logger.error(f"Google Sheets initialization failed: {exc}")
            return False

    def _ensure_header_row(self) -> None:
        """Create header row if the sheet is empty."""
        try:
            result = (
                self._service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self._spreadsheet_id,
                    range=f"{self._sheet_name}!A1:A1",
                )
                .execute()
            )
            existing = result.get("values", [])
            if not existing:
                self._service.spreadsheets().values().update(
                    spreadsheetId=self._spreadsheet_id,
                    range=f"{self._sheet_name}!A1",
                    valueInputOption="RAW",
                    body={"values": [SHEET_COLUMNS]},
                ).execute()
                logger.info("Header row written to Google Sheet.")
        except Exception as exc:
            logger.error(f"Failed to ensure header row: {exc}")

    def _business_to_row(self, b: Business) -> List[str]:
        """Convert a Business ORM object to a sheet row."""
        def fmt_dt(dt):
            return dt.strftime("%Y-%m-%d %H:%M") if dt else ""

        def safe_str(val):
            if val is None:
                return ""
            if isinstance(val, bool):
                return "Yes" if val else "No"
            if isinstance(val, (int, float)):
                return str(val)
            return str(val)

        score_breakdown = ""
        if b.score_breakdown:
            try:
                score_breakdown = json.dumps(b.score_breakdown)
            except Exception:
                score_breakdown = str(b.score_breakdown)

        return [
            safe_str(b.id),
            safe_str(b.business_name),
            safe_str(b.category),
            safe_str(b.area),
            safe_str(b.address),
            safe_str(b.phone),
            safe_str(b.google_maps_url),
            safe_str(b.website),
            safe_str(b.website_status),
            safe_str(b.website_quality),
            safe_str(b.instagram_url),
            safe_str(b.facebook_url),
            safe_str(b.google_rating),
            safe_str(b.google_review_count),
            safe_str(b.booking_link),
            safe_str(b.lead_score),
            safe_str(b.lead_priority),
            score_breakdown,
            safe_str(b.place_id),
            safe_str(b.data_id),
            safe_str(b.business_status),
            fmt_dt(b.first_seen),
            fmt_dt(b.last_checked),
            safe_str(b.contacted),
            fmt_dt(b.contact_date),
            safe_str(b.contact_status),
            fmt_dt(b.follow_up_date),
            safe_str(b.notes),
            safe_str(b.source),
        ]

    def sync_businesses(
        self, businesses: List[Business]
    ) -> Dict[str, Any]:
        """
        Full sync: clear sheet data rows, rewrite all businesses.
        Returns summary dict.
        """
        if not self._ensure_initialized():
            return {"success": False, "error": "Google Sheets not configured", "synced": 0}

        try:
            self._ensure_header_row()

            # Clear existing data (keep header)
            clear_range = f"{self._sheet_name}!A2:Z100000"
            self._service.spreadsheets().values().clear(
                spreadsheetId=self._spreadsheet_id,
                range=clear_range,
            ).execute()

            if not businesses:
                return {"success": True, "synced": 0}

            rows = [self._business_to_row(b) for b in businesses]

            # Batch write
            total_written = 0
            for i in range(0, len(rows), self._batch_size):
                batch = rows[i : i + self._batch_size]
                start_row = i + 2  # row 1 = header
                range_name = f"{self._sheet_name}!A{start_row}"
                self._service.spreadsheets().values().update(
                    spreadsheetId=self._spreadsheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    body={"values": batch},
                ).execute()
                total_written += len(batch)
                logger.info(f"Sheet sync: wrote rows {start_row}–{start_row + len(batch) - 1}.")

            logger.info(f"Google Sheets sync complete: {total_written} rows.")
            return {"success": True, "synced": total_written}

        except Exception as exc:
            logger.error(f"Google Sheets sync failed: {exc}")
            return {"success": False, "error": str(exc), "synced": 0}

    def append_businesses(
        self, businesses: List[Business]
    ) -> Dict[str, Any]:
        """Append new rows without clearing existing data."""
        if not self._ensure_initialized():
            return {"success": False, "error": "Google Sheets not configured", "synced": 0}

        try:
            self._ensure_header_row()
            rows = [self._business_to_row(b) for b in businesses]
            if not rows:
                return {"success": True, "synced": 0}

            self._service.spreadsheets().values().append(
                spreadsheetId=self._spreadsheet_id,
                range=f"{self._sheet_name}!A1",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": rows},
            ).execute()

            logger.info(f"Appended {len(rows)} rows to Google Sheets.")
            return {"success": True, "synced": len(rows)}
        except Exception as exc:
            logger.error(f"Google Sheets append failed: {exc}")
            return {"success": False, "error": str(exc), "synced": 0}

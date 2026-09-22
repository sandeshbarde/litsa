"""
Duplicate detection service.
Uses place_id, data_id, phone, name+area, and fuzzy matching.
"""

from typing import Optional, List, Tuple
from rapidfuzz import fuzz
from loguru import logger

from app.utils.normalization import (
    normalize_business_name,
    normalize_phone,
    normalize_address,
)

# Fuzzy match threshold (0–100)
FUZZY_THRESHOLD = 85


class DeduplicationService:
    """
    Manages in-memory sets of known identifiers for fast dedup
    during a processing run. Persistent dedup is done via DB lookups.
    """

    def __init__(self):
        self._place_ids: set = set()
        self._data_ids: set = set()
        self._phones: set = set()
        self._name_area_pairs: List[Tuple[str, str]] = []

    def load_from_db(
        self,
        place_ids: List[str],
        data_ids: List[str],
        phones: List[str],
        name_area_pairs: List[Tuple[str, str]],
    ) -> None:
        """Pre-load known identifiers from database."""
        self._place_ids = set(pid for pid in place_ids if pid)
        self._data_ids = set(did for did in data_ids if did)
        self._phones = set(p for p in phones if p)
        self._name_area_pairs = [(n, a) for n, a in name_area_pairs if n]
        logger.info(
            f"Dedup loaded: {len(self._place_ids)} place_ids, "
            f"{len(self._phones)} phones, {len(self._name_area_pairs)} names."
        )

    def is_duplicate(
        self,
        place_id: Optional[str] = None,
        data_id: Optional[str] = None,
        phone: Optional[str] = None,
        business_name: Optional[str] = None,
        area: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Returns (is_duplicate, reason).
        Checks in priority order:
        1. place_id
        2. data_id
        3. normalized phone
        4. fuzzy name + area match
        """
        # 1. place_id (strongest signal)
        if place_id and place_id in self._place_ids:
            return True, f"duplicate place_id={place_id}"

        # 2. data_id
        if data_id and data_id in self._data_ids:
            return True, f"duplicate data_id={data_id}"

        # 3. Normalized phone
        norm_phone = normalize_phone(phone)
        if norm_phone and norm_phone in self._phones:
            return True, f"duplicate phone={norm_phone}"

        # 4. Fuzzy name + area
        if business_name and area:
            norm_name = normalize_business_name(business_name)
            norm_area = (area or "").lower().strip()
            for known_name, known_area in self._name_area_pairs:
                if (known_area or "").lower().strip() != norm_area:
                    continue
                score = fuzz.ratio(norm_name, known_name)
                if score >= FUZZY_THRESHOLD:
                    return True, f"fuzzy name match score={score} ({known_name!r})"

        return False, ""

    def register(
        self,
        place_id: Optional[str] = None,
        data_id: Optional[str] = None,
        phone: Optional[str] = None,
        business_name: Optional[str] = None,
        area: Optional[str] = None,
    ) -> None:
        """Register a new business to prevent future duplicates in this run."""
        if place_id:
            self._place_ids.add(place_id)
        if data_id:
            self._data_ids.add(data_id)
        norm_phone = normalize_phone(phone)
        if norm_phone:
            self._phones.add(norm_phone)
        if business_name:
            norm_name = normalize_business_name(business_name)
            self._name_area_pairs.append((norm_name, (area or "").lower().strip()))

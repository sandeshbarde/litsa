"""
Unit tests for deduplication service.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.deduplication import DeduplicationService


def test_duplicate_by_place_id():
    dedup = DeduplicationService()
    dedup.load_from_db(
        place_ids=["ChIJ123"],
        data_ids=[],
        phones=[],
        name_area_pairs=[],
    )
    is_dup, reason = dedup.is_duplicate(place_id="ChIJ123")
    assert is_dup is True
    assert "place_id" in reason


def test_duplicate_by_phone():
    dedup = DeduplicationService()
    dedup.load_from_db(
        place_ids=[],
        data_ids=[],
        phones=["501234567"],
        name_area_pairs=[],
    )
    is_dup, reason = dedup.is_duplicate(phone="+971 50 123 4567")
    assert is_dup is True


def test_not_duplicate_different_area():
    dedup = DeduplicationService()
    dedup.load_from_db(
        place_ids=[],
        data_ids=[],
        phones=[],
        name_area_pairs=[("dubai salon", "deira")],
    )
    is_dup, _ = dedup.is_duplicate(
        business_name="Dubai Salon LLC",
        area="Al Barsha",
    )
    assert is_dup is False


def test_fuzzy_duplicate_same_area():
    dedup = DeduplicationService()
    dedup.load_from_db(
        place_ids=[],
        data_ids=[],
        phones=[],
        name_area_pairs=[("dubai salon", "deira")],
    )
    is_dup, reason = dedup.is_duplicate(
        business_name="Dubai Salon",  # Very similar
        area="Deira",
    )
    assert is_dup is True
    assert "fuzzy" in reason


def test_register_prevents_future_duplicate():
    dedup = DeduplicationService()
    dedup.load_from_db([], [], [], [])
    is_dup, _ = dedup.is_duplicate(place_id="NEW123")
    assert is_dup is False
    dedup.register(place_id="NEW123")
    is_dup2, _ = dedup.is_duplicate(place_id="NEW123")
    assert is_dup2 is True


def test_no_duplicate_for_new_business():
    dedup = DeduplicationService()
    dedup.load_from_db(
        place_ids=["ChIJ999"],
        data_ids=[],
        phones=["501111111"],
        name_area_pairs=[("existing salon", "deira")],
    )
    is_dup, _ = dedup.is_duplicate(
        place_id="ChIJNEW",
        phone="+971 55 999 8888",
        business_name="Completely Different Shop",
        area="Jumeirah",
    )
    assert is_dup is False

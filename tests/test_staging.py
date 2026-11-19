from datetime import date
from src.transformation.staging import compute_age, is_stale_member, enrich_staging_records


def test_compute_age_handles_birthday_before_and_after_as_of():
    assert compute_age(date(1985, 5, 3), as_of=date(2026, 5, 2)) == 40
    assert compute_age(date(1985, 5, 3), as_of=date(2026, 5, 3)) == 41
    assert compute_age(None, as_of=date(2026, 5, 3)) is None


def test_is_stale_member_uses_90_day_threshold():
    ref = date(2026, 11, 19)
    assert is_stale_member(date(2026, 8, 21), as_of=ref) is False  # exactly 90 days
    assert is_stale_member(date(2026, 8, 20), as_of=ref) is True   # 91 days
    assert is_stale_member(None, as_of=ref) is True


def test_enrich_staging_records_adds_derived_columns():
    records = [{"member_id": "223457", "dob": date(1985, 5, 3), "last_flight_date": date(2012, 10, 13)}]
    enriched = enrich_staging_records(records, as_of=date(2026, 11, 19))
    assert enriched[0]["age"] == 41
    assert enriched[0]["stale_member"] is True

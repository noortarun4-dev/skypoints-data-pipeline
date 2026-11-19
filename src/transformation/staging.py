from datetime import date
from typing import Any

from src.config import STALE_DAYS_THRESHOLD


def compute_age(dob: date | None, as_of: date) -> int | None:
    if dob is None:
        return None
    years = as_of.year - dob.year - ((as_of.month, as_of.day) < (dob.month, dob.day))
    return max(years, 0)


def is_stale_member(last_flight_date: date | None, as_of: date) -> bool:
    if last_flight_date is None:
        return True
    return (as_of - last_flight_date).days > STALE_DAYS_THRESHOLD


def enrich_staging_records(
    records: list[dict[str, Any]],
    as_of: date | None = None,
) -> list[dict[str, Any]]:
    """
    Add derived staging columns:
      - age: computed from DOB relative to as_of date
      - stale_member: True when days since last_flight_date > 90 (or no flight recorded)
    """
    ref_date = as_of or date.today()
    enriched: list[dict[str, Any]] = []

    for rec in records:
        row = dict(rec)
        row["age"] = compute_age(rec.get("dob"), ref_date)
        row["stale_member"] = is_stale_member(rec.get("last_flight_date"), ref_date)
        enriched.append(row)

    return enriched

from datetime import date
from typing import Any


def resolve_latest_members(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Apply 'latest record wins' per member_id.
    Tie-breaking order:
      1. Most recent activity date: COALESCE(last_flight_date, enrollment_date)
      2. Most recent enrollment_date
      3. Later arrival order in the feed
    If a member moves countries (e.g., IND -> USA), only the latest country record survives.
    """
    latest_by_id: dict[str, tuple[tuple[date, date, int], dict[str, Any]]] = {}

    for idx, rec in enumerate(records):
        member_id = rec["member_id"]
        activity_date = rec.get("last_flight_date") or rec["enrollment_date"]
        enroll_date = rec["enrollment_date"]
        rank_key = (activity_date, enroll_date, idx)

        if member_id not in latest_by_id or rank_key >= latest_by_id[member_id][0]:
            latest_by_id[member_id] = (rank_key, rec)

    return [entry[1] for entry in latest_by_id.values()]


def split_by_country(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    Resolve latest record per member_id, then partition into per-country buckets
    keyed by normalized ISO-3 country code (USA, IND, AUS, CAN, PHL).
    """
    deduped = resolve_latest_members(records)
    buckets: dict[str, list[dict[str, Any]]] = {}

    for rec in deduped:
        country = rec["country_iso3"]
        buckets.setdefault(country, []).append(rec)

    return buckets

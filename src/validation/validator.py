import logging
from datetime import date, datetime
from typing import Any

from src.config import COUNTRY_CODE_MAP, VALID_ACTIVE_FLAGS, VALID_TIER_CODES

logger = logging.getLogger(__name__)


def parse_flexible_date(raw_val: str | None, field_name: str, source_file: str = "") -> date | None:
    """
    Parse dates across heterogeneous source formats:
      - ISO: YYYY-MM-DD (AUS.xlsx)
      - Slash: M/D/YYYY (IND.csv)
      - Flat file: YYYYMMDD for enrollment/flight, DDMMYYYY (or 7-digit zero-truncated) for DOB
      - USA.csv: unpadded MMDDYYYY integers (e.g., 6152022 -> 06152022)
    Returns None if raw_val is None/empty; raises ValueError if unparseable.
    """
    if raw_val is None or str(raw_val).strip() == "":
        return None

    val = str(raw_val).strip()

    # Strip Excel timestamp suffix if pandas read a datetime cell (e.g. '2022-05-11 00:00:00')
    if " " in val:
        val = val.split(" ")[0]

    # 1. ISO format (YYYY-MM-DD)
    if "-" in val:
        return datetime.strptime(val, "%Y-%m-%d").date()

    # 2. Slash format (M/D/YYYY in IND.csv)
    if "/" in val:
        return datetime.strptime(val, "%m/%d/%Y").date()

    # 3. Pure digits (flat file or USA.csv)
    if val.isdigit():
        padded = val.zfill(8)
        if source_file.upper().startswith("USA"):
            return datetime.strptime(padded, "%m%d%Y").date()
        if field_name == "dob":
            return datetime.strptime(padded, "%d%m%Y").date()
        # Flat-file enrollment_date / last_flight_date -> YYYYMMDD
        return datetime.strptime(padded, "%Y%m%d").date()

    raise ValueError(f"Unrecognized date format '{raw_val}' for {field_name}")


def validate_records(
    records: list[dict[str, Any]],
    enforce_unique_key: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Validate raw member records against data quality rules:
      1. Mandatory fields: member_id, member_name, enrollment_date, country
      2. Valid date parsing (catches invalid dates like 2021-13-13)
      3. Country code normalization (AU->AUS, PHIL->PHL)
      4. Valid tier_code and is_active domain values
      5. Optional batch-level member_id uniqueness check
    Returns (valid_records, quarantined_records).
    """
    valid_records: list[dict[str, Any]] = []
    quarantined_records: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for rec in records:
        reasons: list[str] = []
        source_file = rec.get("_source_file") or ""

        # 1. Mandatory checks
        if not rec.get("member_id"):
            reasons.append("missing_member_id")
        if not rec.get("member_name"):
            reasons.append("missing_member_name")
        if not rec.get("enrollment_date"):
            reasons.append("missing_enrollment_date")
        if not rec.get("country"):
            reasons.append("missing_country")

        # 2. Country normalization
        country_raw = (rec.get("country") or "").strip().upper()
        country_iso3 = COUNTRY_CODE_MAP.get(country_raw)
        if country_raw and not country_iso3:
            reasons.append(f"unknown_country_code:{country_raw}")

        # 3. Date parsing
        parsed_enroll = None
        if rec.get("enrollment_date"):
            try:
                parsed_enroll = parse_flexible_date(rec["enrollment_date"], "enrollment_date", source_file)
            except ValueError:
                reasons.append(f"invalid_enrollment_date:{rec['enrollment_date']}")

        parsed_flight = None
        if rec.get("last_flight_date"):
            try:
                parsed_flight = parse_flexible_date(rec["last_flight_date"], "last_flight_date", source_file)
            except ValueError:
                reasons.append(f"invalid_last_flight_date:{rec['last_flight_date']}")

        parsed_dob = None
        if rec.get("dob"):
            try:
                parsed_dob = parse_flexible_date(rec["dob"], "dob", source_file)
            except ValueError:
                reasons.append(f"invalid_dob:{rec['dob']}")

        # 4. Domain value checks
        tier = (rec.get("tier_code") or "").strip().upper() or None
        if tier and tier not in VALID_TIER_CODES:
            reasons.append(f"invalid_tier_code:{tier}")

        flag = (rec.get("is_active") or "").strip().upper() or None
        if flag and flag not in VALID_ACTIVE_FLAGS:
            reasons.append(f"invalid_is_active:{flag}")

        # 5. Key uniqueness check (when enabled for single-feed batches)
        member_id = rec.get("member_id")
        if enforce_unique_key and member_id:
            if member_id in seen_keys:
                reasons.append(f"duplicate_member_id:{member_id}")
            else:
                seen_keys.add(member_id)

        if reasons:
            quarantined_records.append({
                "raw_member_id": rec.get("member_id"),
                "raw_member_name": rec.get("member_name"),
                "raw_country": rec.get("country"),
                "failure_reasons": "; ".join(reasons),
                "_source_file": source_file,
            })
        else:
            cleaned = dict(rec)
            cleaned["enrollment_date"] = parsed_enroll
            cleaned["last_flight_date"] = parsed_flight
            cleaned["dob"] = parsed_dob
            cleaned["country_raw"] = country_raw
            cleaned["country_iso3"] = country_iso3
            cleaned["tier_code"] = tier
            cleaned["is_active"] = flag
            valid_records.append(cleaned)

    logger.info(
        "Validation complete: %d valid, %d quarantined",
        len(valid_records),
        len(quarantined_records),
    )
    return valid_records, quarantined_records

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

HEADER_TO_CANONICAL = {
    "member_name": "member_name",
    "member_id": "member_id",
    "enrollment_date": "enrollment_date",
    "last_flight_date": "last_flight_date",
    "tier_code": "tier_code",
    "agent_name": "agent_name",
    "state": "state",
    "country": "country",
    "post_code": "post_code",
    "dob": "dob",
    "date_of_birth": "dob",
    "is_active": "is_active",
    "active_member": "is_active",
}

CANONICAL_FIELDS = [
    "member_id",
    "member_name",
    "enrollment_date",
    "last_flight_date",
    "tier_code",
    "agent_name",
    "state",
    "country",
    "post_code",
    "dob",
    "is_active",
    "member_type",
]


def _clean_value(val: str | None) -> str | None:
    if val is None:
        return None
    stripped = val.strip()
    if stripped == "" or stripped.upper() == "NULL":
        return None
    return stripped


def parse_flat_file(file_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    headers: list[str] = []

    with open(file_path, "r", encoding="utf-8") as fh:
        for line_num, raw_line in enumerate(fh, start=1):
            line = raw_line.strip()
            if not line:
                continue

            parts = [p for p in line.split("|")]
            if parts and parts[0] == "":
                parts = parts[1:]

            if not parts:
                continue

            record_type = parts[0].strip().upper()
            values = parts[1:]

            if record_type == "H":
                headers = [
                    HEADER_TO_CANONICAL.get(col.strip().lower(), col.strip().lower())
                    for col in values
                ]
                logger.info("Parsed flat-file header (%d columns) from %s", len(headers), file_path.name)
            elif record_type == "D":
                if not headers:
                    raise ValueError(f"Detail record found before header at line {line_num} in {file_path}")
                row: dict[str, Any] = {field: None for field in CANONICAL_FIELDS}
                for idx, col_name in enumerate(headers):
                    if idx < len(values) and col_name in row:
                        row[col_name] = _clean_value(values[idx])
                row["_source_file"] = file_path.name
                records.append(row)
            else:
                logger.warning("Skipping unknown record type '%s' at line %d", record_type, line_num)

    return records

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.ingestion.flat_file_parser import CANONICAL_FIELDS, _clean_value

logger = logging.getLogger(__name__)

COUNTRY_COLUMN_MAP = {
    "unique id": "member_id",
    "id": "member_id",
    "member name": "member_name",
    "name": "member_name",
    "tier type": "tier_code",
    "tiercode": "tier_code",
    "date of birth": "dob",
    "dob": "dob",
    "date of enrollment": "enrollment_date",
    "enrollmentdate": "enrollment_date",
    "date of flight": "last_flight_date",
    "flightdate": "last_flight_date",
    "flight date": "last_flight_date",
    "individual or corporate": "member_type",
}


def load_country_file(file_path: Path, country_code: str) -> list[dict[str, Any]]:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, dtype=str, keep_default_na=False)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

    records: list[dict[str, Any]] = []
    for _, raw_row in df.iterrows():
        row: dict[str, Any] = {field: None for field in CANONICAL_FIELDS}
        for col_name, val in raw_row.items():
            canonical = COUNTRY_COLUMN_MAP.get(str(col_name).strip().lower())
            if canonical:
                row[canonical] = _clean_value(str(val))

        if row["member_id"] is not None:
            row["member_id"] = f"{country_code.upper()}-{row['member_id']}"

        row["country"] = country_code.upper()
        row["is_active"] = "A"
        row["_source_file"] = file_path.name
        records.append(row)

    logger.info("Loaded %d records from %s", len(records), file_path.name)
    return records

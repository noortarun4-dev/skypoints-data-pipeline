import logging
from datetime import date
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from src.config import COUNTRY_TABLE_MAP, DB_PATH, OUTPUT_DIR, RAW_DATA_DIR
from src.ingestion.file_loader import load_country_file
from src.ingestion.flat_file_parser import parse_flat_file
from src.ingestion.json_parser import parse_redemptions_json
from src.transformation.country_router import split_by_country
from src.transformation.staging import enrich_staging_records
from src.validation.validator import validate_records

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def run_pipeline(
    raw_dir: Path = RAW_DATA_DIR,
    db_path: Path = DB_PATH,
    as_of: date | None = None,
) -> dict[str, Any]:
    """End-to-end local execution of the SkyPoints ETL pipeline using DuckDB."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_records: list[dict[str, Any]] = []

    flat_file = raw_dir / "members_feed.txt"
    if flat_file.exists():
        raw_records.extend(parse_flat_file(flat_file))

    country_files = [
        ("AUS.xlsx", "AUS"),
        ("USA.csv", "USA"),
        ("IND.csv", "IND"),
    ]
    for filename, code in country_files:
        fpath = raw_dir / filename
        if fpath.exists():
            raw_records.extend(load_country_file(fpath, country_code=code))

    valid_records, quarantined_records = validate_records(raw_records)
    staged_records = enrich_staging_records(valid_records, as_of=as_of)
    country_buckets = split_by_country(staged_records)

    redemptions_file = raw_dir / "redemptions_feed.json"
    redemptions = parse_redemptions_json(redemptions_file) if redemptions_file.exists() else []

    con = duckdb.connect(str(db_path))
    try:
        # 1. Staging & Quarantine tables
        stg_df = pd.DataFrame(staged_records)
        con.register("stg_df", stg_df)
        con.execute("CREATE OR REPLACE TABLE stg_members AS SELECT * FROM stg_df")

        if quarantined_records:
            q_df = pd.DataFrame(quarantined_records)
            con.register("q_df", q_df)
            con.execute("CREATE OR REPLACE TABLE quarantine_members AS SELECT * FROM q_df")
        else:
            con.execute("CREATE OR REPLACE TABLE quarantine_members (raw_member_id VARCHAR, failure_reasons VARCHAR)")

        # 2. Country target tables
        created_country_tables: list[str] = []
        for iso3, rows in country_buckets.items():
            table_name = COUNTRY_TABLE_MAP.get(iso3, f"table_{iso3.lower()}")
            cdf = pd.DataFrame(rows)
            con.register("cdf", cdf)
            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM cdf")
            created_country_tables.append(table_name)

        # 3. Unified member view
        if created_country_tables:
            union_sql = " UNION ALL ".join(f"SELECT * FROM {t}" for t in created_country_tables)
            con.execute(f"CREATE OR REPLACE VIEW vw_all_members AS {union_sql}")

        # 4. Flattened redemptions table + analytical join view
        if redemptions:
            red_df = pd.DataFrame(redemptions)
            con.register("red_df", red_df)
            con.execute("CREATE OR REPLACE TABLE fact_redemptions AS SELECT * FROM red_df")

            con.execute("""
                CREATE OR REPLACE VIEW vw_member_redemption_summary AS
                SELECT
                    m.member_id,
                    m.member_name,
                    m.country_iso3,
                    m.tier_code,
                    m.age,
                    m.stale_member,
                    COUNT(r.txn_id) AS total_redemptions,
                    COALESCE(SUM(CASE WHEN r.status = 'COMPLETED' THEN r.miles_redeemed ELSE 0 END), 0) AS completed_miles
                FROM vw_all_members AS m
                LEFT JOIN fact_redemptions AS r ON m.member_id = r.member_id
                GROUP BY 1, 2, 3, 4, 5, 6
            """)

        summary = {
            "raw_count": len(raw_records),
            "valid_count": len(valid_records),
            "quarantined_count": len(quarantined_records),
            "country_counts": {k: len(v) for k, v in country_buckets.items()},
            "redemptions_count": len(redemptions),
            "db_path": str(db_path),
        }
        logger.info("Pipeline completed successfully: %s", summary)
        return summary
    finally:
        con.close()


if __name__ == "__main__":
    result = run_pipeline()
    print("\n=== SkyPoints Pipeline Summary ===")
    for k, v in result.items():
        print(f"  {k}: {v}")

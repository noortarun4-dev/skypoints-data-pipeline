from datetime import date
import duckdb

from src.ingestion.json_parser import parse_redemptions_json
from src.pipeline import run_pipeline


def test_parse_redemptions_json_flattens_nested_transactions(tmp_path):
    feed = tmp_path / "redemptions.json"
    feed.write_text(
        '{"member_id":"223457","feed_date":"20240115","redemptions":['
        '{"txn_id":"RX10091","txn_date":"20240110","partner":"AeroLink","miles_redeemed":12000,"status":"COMPLETED"},'
        '{"txn_id":"RX10092","txn_date":"20240113","partner":"SkyPoints","miles_redeemed":5000,"status":"PENDING"}'
        ']}',
        encoding="utf-8",
    )

    rows = parse_redemptions_json(feed)
    assert len(rows) == 2
    assert rows[0]["member_id"] == "223457"
    assert rows[0]["miles_redeemed"] == 12000


def test_end_to_end_pipeline_builds_country_tables_and_joins_redemptions(tmp_path):
    db_file = tmp_path / "test_skypoints.duckdb"
    summary = run_pipeline(db_path=db_file, as_of=date(2026, 11, 19))

    assert summary["valid_count"] >= 5
    assert summary["redemptions_count"] == 2

    con = duckdb.connect(str(db_file))
    try:
        elena = con.execute(
            "SELECT member_name, country_iso3, total_redemptions, completed_miles "
            "FROM vw_member_redemption_summary WHERE member_id = '223457'"
        ).fetchone()
        assert elena == ("Elena", "USA", 2, 12000)
    finally:
        con.close()

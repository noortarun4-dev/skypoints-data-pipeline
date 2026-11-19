from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "output"
DB_PATH = OUTPUT_DIR / "skypoints.duckdb"

STALE_DAYS_THRESHOLD = 90

COUNTRY_CODE_MAP = {
    "USA": "USA",
    "US": "USA",
    "IND": "IND",
    "IN": "IND",
    "AU": "AUS",
    "AUS": "AUS",
    "CAN": "CAN",
    "CA": "CAN",
    "PHIL": "PHL",
    "PHL": "PHL",
    "PH": "PHL",
}

COUNTRY_TABLE_MAP = {
    "USA": "table_usa",
    "IND": "table_india",
    "AUS": "table_australia",
    "CAN": "table_canada",
    "PHL": "table_philippines",
}

VALID_TIER_CODES = {"SLV", "GLD", "PLT"}
VALID_ACTIVE_FLAGS = {"A", "I"}

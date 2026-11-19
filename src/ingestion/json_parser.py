import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def parse_redemptions_json(file_path: Path) -> list[dict[str, Any]]:
    """
    Flatten semi-structured partner airline redemption JSON feed into
    queryable transaction-level rows (deduplicated by txn_id).
    Supports both a single JSON object and a JSON array of member payloads.
    """
    raw_data = json.loads(file_path.read_text(encoding="utf-8"))
    payloads = raw_data if isinstance(raw_data, list) else [raw_data]

    flattened: dict[str, dict[str, Any]] = {}
    for entry in payloads:
        member_id = str(entry["member_id"]).strip()
        feed_date = datetime.strptime(str(entry["feed_date"]), "%Y%m%d").date()

        for txn in entry.get("redemptions", []):
            txn_id = str(txn["txn_id"]).strip()
            flattened[txn_id] = {
                "txn_id": txn_id,
                "member_id": member_id,
                "feed_date": feed_date,
                "txn_date": datetime.strptime(str(txn["txn_date"]), "%Y%m%d").date(),
                "partner": str(txn["partner"]).strip(),
                "miles_redeemed": int(txn["miles_redeemed"]),
                "status": str(txn["status"]).strip().upper(),
            }

    logger.info("Flattened %d redemption transactions from %s", len(flattened), file_path.name)
    return list(flattened.values())

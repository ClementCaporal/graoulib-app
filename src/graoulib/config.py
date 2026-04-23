from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

GBFS_ENTRYPOINT_URL = "https://gbfs.partners.fifteen.eu/gbfs/metz/gbfs.json"
REQUEST_TIMEOUT_SECONDS = 20

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HISTORY_DIR = PROJECT_ROOT / "data" / "history"
DOCS_DATA_DIR = PROJECT_ROOT / "docs" / "data"

LOCAL_TIMEZONE = ZoneInfo("Europe/Paris")


def history_file_for_timestamp(timestamp_utc: str) -> Path:
    parsed = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))
    local_day = parsed.astimezone(LOCAL_TIMEZONE).date().isoformat()
    return HISTORY_DIR / f"{local_day}.ndjson"

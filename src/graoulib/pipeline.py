from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DOCS_DATA_DIR, HISTORY_DIR, LOCAL_TIMEZONE
from .fetcher import fetch_station_snapshot
from .storage import append_snapshot_to_history


def collect_and_store_snapshot() -> tuple[dict[str, Any], Path]:
    snapshot = fetch_station_snapshot()
    history_file = append_snapshot_to_history(snapshot)
    return snapshot, history_file


def _history_files(date_str: str | None) -> list[Path]:
    if date_str:
        return [HISTORY_DIR / f"{date_str}.ndjson"]
    return sorted(HISTORY_DIR.glob("*.ndjson"))


def _aggregate_history(history_files: list[Path]) -> dict[str, Any]:
    stations_by_id: dict[str, dict[str, Any]] = {}
    timestamps: list[str] = []

    for history_file in history_files:
        if not history_file.exists():
            continue

        with history_file.open("r", encoding="utf-8") as input_file:
            for line in input_file:
                line = line.strip()
                if not line:
                    continue

                snapshot = json.loads(line)
                timestamp = snapshot.get("fetched_at_utc")
                if not isinstance(timestamp, str):
                    continue

                timestamps.append(timestamp)
                for station in snapshot.get("stations", []):
                    station_id = str(station.get("station_id", "unknown"))
                    current = stations_by_id.setdefault(
                        station_id,
                        {
                            "station_id": station_id,
                            "name": station.get("name", "unknown"),
                            "lat": station.get("lat"),
                            "lon": station.get("lon"),
                            "capacity": station.get("capacity"),
                            "series": [],
                        },
                    )
                    current["series"].append(
                        {
                            "timestamp": timestamp,
                            "num_bikes_available": station.get("num_bikes_available"),
                            "num_docks_available": station.get("num_docks_available"),
                        }
                    )

    for station in stations_by_id.values():
        station["series"].sort(key=lambda item: str(item.get("timestamp", "")))

    sorted_timestamps = sorted(set(timestamps))
    return {
        "snapshot_count": len(timestamps),
        "timestamps": sorted_timestamps,
        "stations": sorted(stations_by_id.values(), key=lambda station: str(station.get("name", ""))),
        "range_start": sorted_timestamps[0] if sorted_timestamps else None,
        "range_end": sorted_timestamps[-1] if sorted_timestamps else None,
    }


def build_daily_series(date_str: str | None = None) -> dict[str, Any]:
    if date_str:
        target_day = date_str
        output_filename = "today_series.json"
    else:
        target_day = "all history"
        output_filename = "all_series.json"

    aggregated = _aggregate_history(_history_files(date_str))

    payload = {
        "date": target_day,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "snapshot_count": aggregated["snapshot_count"],
        "timestamps": aggregated["timestamps"],
        "stations": aggregated["stations"],
        "range_start": aggregated["range_start"],
        "range_end": aggregated["range_end"],
    }

    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DATA_DIR / output_filename).write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )

    return payload

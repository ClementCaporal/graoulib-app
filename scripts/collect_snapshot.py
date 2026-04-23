#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from graoulib.pipeline import collect_and_store_snapshot


if __name__ == "__main__":
    snapshot, history_file = collect_and_store_snapshot()
    station_count = len(snapshot.get("stations", []))
    print(f"Stored snapshot with {station_count} stations in {history_file}")

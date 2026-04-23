#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from graoulib.pipeline import build_daily_series


def main() -> None:
    parser = argparse.ArgumentParser(description="Build docs/data/today_series.json from history")
    parser.add_argument("--date", help="Date to aggregate, format YYYY-MM-DD", default=None)
    args = parser.parse_args()

    payload = build_daily_series(date_str=args.date)
    print(
        "Built today_series.json "
        f"(date={payload['date']}, snapshots={payload['snapshot_count']}, stations={len(payload['stations'])})"
    )


if __name__ == "__main__":
    main()

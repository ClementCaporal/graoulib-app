#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from graoulib.pipeline import collect_and_store_snapshot


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_once() -> None:
    snapshot, history_file = collect_and_store_snapshot()
    station_count = len(snapshot.get("stations", []))
    print(
        f"[{utc_now()}] Stored snapshot with {station_count} stations in {history_file}",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Continuously collect bike station snapshots at a fixed interval"
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=600,
        help="Delay between collections in seconds (default: 600)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single collection and exit",
    )
    args = parser.parse_args()

    if args.interval_seconds <= 0:
        raise ValueError("--interval-seconds must be > 0")

    run_once()
    if args.once:
        return

    print(
        f"[{utc_now()}] Collector loop started (interval={args.interval_seconds}s). Press Ctrl+C to stop.",
        flush=True,
    )
    while True:
        try:
            time.sleep(args.interval_seconds)
            run_once()
        except KeyboardInterrupt:
            print(f"[{utc_now()}] Collector loop stopped by user.", flush=True)
            return
        except Exception as error:
            print(f"[{utc_now()}] Collection error: {error}", flush=True)


if __name__ == "__main__":
    main()

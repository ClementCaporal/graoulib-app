from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import DOCS_DATA_DIR, history_file_for_timestamp


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def append_snapshot_to_history(snapshot: dict[str, Any]) -> Path:
    timestamp = snapshot["fetched_at_utc"]
    target_file = history_file_for_timestamp(timestamp)

    target_file.parent.mkdir(parents=True, exist_ok=True)
    with target_file.open("a", encoding="utf-8") as output:
        output.write(json.dumps(snapshot, ensure_ascii=True, separators=(",", ":")) + "\n")

    latest_snapshot_path = target_file.parent.parent / "latest_snapshot.json"
    _write_json(latest_snapshot_path, snapshot)
    _write_json(DOCS_DATA_DIR / "latest_snapshot.json", snapshot)

    return target_file

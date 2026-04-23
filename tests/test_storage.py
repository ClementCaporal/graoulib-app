from __future__ import annotations

import json
from pathlib import Path

from graoulib import storage


def test_append_snapshot_to_history_writes_history_and_latest(tmp_path, monkeypatch):
    history_path = tmp_path / "history" / "2026-04-23.ndjson"
    docs_data_dir = tmp_path / "docs" / "data"

    monkeypatch.setattr(storage, "history_file_for_timestamp", lambda _ts: history_path)
    monkeypatch.setattr(storage, "DOCS_DATA_DIR", docs_data_dir)

    snapshot = {
        "fetched_at_utc": "2026-04-23T12:10:00Z",
        "source": {"gbfs_root": "x", "station_information": "y", "station_status": "z"},
        "stations": [{"station_id": "1", "name": "Station A", "num_bikes_available": 4}],
    }

    returned_file = storage.append_snapshot_to_history(snapshot)

    assert returned_file == history_path
    assert history_path.exists()

    lines = history_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["fetched_at_utc"] == "2026-04-23T12:10:00Z"

    latest_data_path = tmp_path / "latest_snapshot.json"
    assert latest_data_path.exists()
    assert json.loads(latest_data_path.read_text(encoding="utf-8"))["fetched_at_utc"] == "2026-04-23T12:10:00Z"

    docs_latest_path = docs_data_dir / "latest_snapshot.json"
    assert docs_latest_path.exists()
    assert json.loads(docs_latest_path.read_text(encoding="utf-8"))["fetched_at_utc"] == "2026-04-23T12:10:00Z"

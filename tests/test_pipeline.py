from __future__ import annotations

import json

from graoulib import pipeline


def test_build_daily_series_creates_station_series(tmp_path, monkeypatch):
    history_dir = tmp_path / "history"
    docs_data_dir = tmp_path / "docs" / "data"
    history_dir.mkdir(parents=True, exist_ok=True)

    day = "2026-04-23"
    history_file = history_dir / f"{day}.ndjson"

    first_snapshot = {
        "fetched_at_utc": "2026-04-23T08:00:00Z",
        "stations": [
            {
                "station_id": "1",
                "name": "Station A",
                "lat": 49.1,
                "lon": 6.1,
                "capacity": 20,
                "num_bikes_available": 10,
                "num_docks_available": 10,
            }
        ],
    }
    second_snapshot = {
        "fetched_at_utc": "2026-04-23T08:10:00Z",
        "stations": [
            {
                "station_id": "1",
                "name": "Station A",
                "lat": 49.1,
                "lon": 6.1,
                "capacity": 20,
                "num_bikes_available": 8,
                "num_docks_available": 12,
            }
        ],
    }

    history_file.write_text(
        json.dumps(first_snapshot) + "\n" + json.dumps(second_snapshot) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(pipeline, "HISTORY_DIR", history_dir)
    monkeypatch.setattr(pipeline, "DOCS_DATA_DIR", docs_data_dir)

    payload = pipeline.build_daily_series(date_str=day)

    assert payload["date"] == day
    assert payload["snapshot_count"] == 2
    assert len(payload["stations"]) == 1
    station = payload["stations"][0]
    assert station["station_id"] == "1"
    assert [item["num_bikes_available"] for item in station["series"]] == [10, 8]

    generated_file = docs_data_dir / "today_series.json"
    assert generated_file.exists()
    generated_payload = json.loads(generated_file.read_text(encoding="utf-8"))
    assert generated_payload["snapshot_count"] == 2


def test_build_daily_series_without_date_concatenates_all_history(tmp_path, monkeypatch):
    history_dir = tmp_path / "history"
    docs_data_dir = tmp_path / "docs" / "data"
    history_dir.mkdir(parents=True, exist_ok=True)

    day_one = history_dir / "2026-04-23.ndjson"
    day_two = history_dir / "2026-04-24.ndjson"

    day_one.write_text(
        json.dumps(
            {
                "fetched_at_utc": "2026-04-23T08:00:00Z",
                "stations": [
                    {
                        "station_id": "1",
                        "name": "Station A",
                        "lat": 49.1,
                        "lon": 6.1,
                        "capacity": 20,
                        "num_bikes_available": 10,
                        "num_docks_available": 10,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    day_two.write_text(
        json.dumps(
            {
                "fetched_at_utc": "2026-04-24T08:10:00Z",
                "stations": [
                    {
                        "station_id": "1",
                        "name": "Station A",
                        "lat": 49.1,
                        "lon": 6.1,
                        "capacity": 20,
                        "num_bikes_available": 8,
                        "num_docks_available": 12,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(pipeline, "HISTORY_DIR", history_dir)
    monkeypatch.setattr(pipeline, "DOCS_DATA_DIR", docs_data_dir)

    payload = pipeline.build_daily_series()

    assert payload["date"] == "all history"
    assert payload["snapshot_count"] == 2
    assert payload["range_start"] == "2026-04-23T08:00:00Z"
    assert payload["range_end"] == "2026-04-24T08:10:00Z"
    assert [item["timestamp"] for item in payload["stations"][0]["series"]] == [
        "2026-04-23T08:00:00Z",
        "2026-04-24T08:10:00Z",
    ]

    generated_file = docs_data_dir / "all_series.json"
    assert generated_file.exists()
    generated_payload = json.loads(generated_file.read_text(encoding="utf-8"))
    assert generated_payload["snapshot_count"] == 2

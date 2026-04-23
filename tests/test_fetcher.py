from __future__ import annotations

from graoulib import fetcher


def test_discover_station_feed_urls_supports_non_fr_language(monkeypatch):
    payload = {
        "data": {
            "en": {
                "feeds": [
                    {"name": "station_information", "url": "https://example.com/info"},
                    {"name": "station_status", "url": "https://example.com/status"},
                ]
            }
        }
    }

    monkeypatch.setattr(fetcher, "fetch_json", lambda _url: payload)

    station_info_url, station_status_url = fetcher.discover_station_feed_urls("https://example.com/root")

    assert station_info_url == "https://example.com/info"
    assert station_status_url == "https://example.com/status"


def test_fetch_station_snapshot_merges_info_and_status(monkeypatch):
    root_url = "https://example.com/root"
    info_url = "https://example.com/info"
    status_url = "https://example.com/status"

    payload_by_url = {
        root_url: {
            "data": {
                "en": {
                    "feeds": [
                        {"name": "station_information", "url": info_url},
                        {"name": "station_status", "url": status_url},
                    ]
                }
            }
        },
        info_url: {
            "data": {
                "stations": [
                    {
                        "station_id": "1",
                        "name": "Station A",
                        "lat": 49.1,
                        "lon": 6.1,
                        "capacity": 20,
                    }
                ]
            }
        },
        status_url: {
            "data": {
                "stations": [
                    {
                        "station_id": "1",
                        "num_bikes_available": 7,
                        "num_docks_available": 13,
                        "is_installed": 1,
                        "is_renting": 1,
                        "is_returning": 1,
                        "last_reported": 1710000000,
                    }
                ]
            }
        },
    }

    monkeypatch.setattr(fetcher, "GBFS_ENTRYPOINT_URL", root_url)
    monkeypatch.setattr(fetcher, "fetch_json", lambda url: payload_by_url[url])

    snapshot = fetcher.fetch_station_snapshot()

    assert "fetched_at_utc" in snapshot
    assert snapshot["source"]["station_information"] == info_url
    assert snapshot["source"]["station_status"] == status_url
    assert len(snapshot["stations"]) == 1
    assert snapshot["stations"][0]["name"] == "Station A"
    assert snapshot["stations"][0]["num_bikes_available"] == 7

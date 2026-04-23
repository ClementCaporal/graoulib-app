from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

from .config import GBFS_ENTRYPOINT_URL, REQUEST_TIMEOUT_SECONDS


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "graoulib-app/0.1 (+https://github.com/)"
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _extract_feeds(gbfs_root: dict[str, Any]) -> list[dict[str, Any]]:
    data = gbfs_root.get("data", {})
    if not isinstance(data, dict):
        return []

    feeds: list[dict[str, Any]] = []
    for value in data.values():
        if not isinstance(value, dict):
            continue
        lang_feeds = value.get("feeds", [])
        if isinstance(lang_feeds, list):
            feeds.extend(feed for feed in lang_feeds if isinstance(feed, dict))
    return feeds


def discover_station_feed_urls(entrypoint_url: str | None = None) -> tuple[str, str]:
    target_url = entrypoint_url or GBFS_ENTRYPOINT_URL
    gbfs_root = fetch_json(target_url)
    feeds = _extract_feeds(gbfs_root)

    station_info_url = ""
    station_status_url = ""

    for feed in feeds:
        feed_name = feed.get("name")
        feed_url = feed.get("url")
        if feed_name == "station_information":
            station_info_url = feed_url
        if feed_name == "station_status":
            station_status_url = feed_url

    if not station_info_url or not station_status_url:
        raise ValueError("Could not discover station_information and station_status URLs from GBFS root")

    return station_info_url, station_status_url


def fetch_station_snapshot() -> dict[str, Any]:
    station_info_url, station_status_url = discover_station_feed_urls()

    info_payload = fetch_json(station_info_url)
    status_payload = fetch_json(station_status_url)

    station_info_list = info_payload.get("data", {}).get("stations", [])
    station_status_list = status_payload.get("data", {}).get("stations", [])

    info_by_id = {
        station.get("station_id"): {
            "station_id": station.get("station_id"),
            "name": station.get("name", "unknown"),
            "lat": station.get("lat"),
            "lon": station.get("lon"),
            "capacity": station.get("capacity"),
        }
        for station in station_info_list
    }

    merged_stations: list[dict[str, Any]] = []
    for status in station_status_list:
        station_id = status.get("station_id")
        info = info_by_id.get(station_id, {"station_id": station_id, "name": "unknown", "lat": None, "lon": None, "capacity": None})
        merged_stations.append(
            {
                **info,
                "num_bikes_available": status.get("num_bikes_available"),
                "num_docks_available": status.get("num_docks_available"),
                "is_installed": status.get("is_installed"),
                "is_renting": status.get("is_renting"),
                "is_returning": status.get("is_returning"),
                "last_reported": status.get("last_reported"),
            }
        )

    fetched_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return {
        "fetched_at_utc": fetched_at_utc,
        "source": {
            "gbfs_root": GBFS_ENTRYPOINT_URL,
            "station_information": station_info_url,
            "station_status": station_status_url,
        },
        "stations": sorted(merged_stations, key=lambda station: str(station.get("name", ""))),
    }

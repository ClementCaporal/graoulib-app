const statusEl = document.getElementById("status");
const metaEl = document.getElementById("meta");
const chartCanvas = document.getElementById("stationChart");
const mapContainer = document.getElementById("stationMap");
const stationTitleEl = document.getElementById("stationTitle");
const heatmapCanvas = document.getElementById("heatmapCanvas");
const heatmapStatusEl = document.getElementById("heatmapStatus");
const snapshotMapContainer = document.getElementById("snapshotMap");
const snapshotSlider = document.getElementById("snapshotSlider");
const snapshotTimeLabelEl = document.getElementById("snapshotTimeLabel");
const snapshotStatusEl = document.getElementById("snapshotStatus");

let chart;
let dailyData;
let map;
let snapshotMap;
const selectedStationIds = new Set();
const markersByStationId = new Map();
const snapshotMarkersByStationId = new Map();

const SERIES_COLORS = [
  "#0c7f6f",
  "#ea580c",
  "#2563eb",
  "#9333ea",
  "#dc2626",
  "#0891b2",
  "#4f46e5",
  "#65a30d",
];

let heatmapGeometry;
let stationSeriesById = new Map();
let snapshotMinBikes = 0;
let snapshotMaxBikes = 1;

function toLocalTime(isoTimestamp) {
  const date = new Date(isoTimestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatTimestampLabel(isoTimestamp) {
  const date = new Date(isoTimestamp);
  return date.toLocaleString([], {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function colorForStationId(stationId) {
  let hash = 0;
  for (let index = 0; index < stationId.length; index += 1) {
    hash = (hash * 31 + stationId.charCodeAt(index)) >>> 0;
  }
  return SERIES_COLORS[hash % SERIES_COLORS.length];
}

function interpolateColor(start, end, t) {
  const clamped = Math.max(0, Math.min(1, t));
  const red = Math.round(start[0] + (end[0] - start[0]) * clamped);
  const green = Math.round(start[1] + (end[1] - start[1]) * clamped);
  const blue = Math.round(start[2] + (end[2] - start[2]) * clamped);
  return `rgb(${red}, ${green}, ${blue})`;
}

function viridisColor(value, min, max) {
  if (!Number.isFinite(value)) {
    return "#e7e0d2";
  }
  if (max <= min) {
    return "#21918c";
  }

  const t = (value - min) / (max - min);
  const stops = [
    { t: 0, rgb: [68, 1, 84] },
    { t: 0.25, rgb: [59, 82, 139] },
    { t: 0.5, rgb: [33, 145, 140] },
    { t: 0.75, rgb: [94, 201, 98] },
    { t: 1, rgb: [253, 231, 37] },
  ];

  for (let index = 0; index < stops.length - 1; index += 1) {
    const current = stops[index];
    const next = stops[index + 1];
    if (t >= current.t && t <= next.t) {
      const ratio = (t - current.t) / (next.t - current.t);
      return interpolateColor(current.rgb, next.rgb, ratio);
    }
  }

  return "#fde725";
}

function buildHeatmap() {
  const timestamps = dailyData.timestamps || [];
  const stations = dailyData.stations || [];

  if (!heatmapCanvas || timestamps.length === 0 || stations.length === 0) {
    return;
  }

  const bikesValues = stations
    .flatMap((station) => station.series.map((item) => item.num_bikes_available))
    .filter((item) => Number.isFinite(item));

  const minValue = bikesValues.length > 0 ? Math.min(...bikesValues) : 0;
  const maxValue = bikesValues.length > 0 ? Math.max(...bikesValues) : 1;

  const cellWidth = 12;
  const cellHeight = 14;
  const leftPadding = 180;
  const topPadding = 28;
  const rightPadding = 20;
  const bottomPadding = 46;

  const logicalWidth = leftPadding + timestamps.length * cellWidth + rightPadding;
  const logicalHeight = topPadding + stations.length * cellHeight + bottomPadding;
  const pixelRatio = window.devicePixelRatio || 1;

  heatmapCanvas.style.width = `${logicalWidth}px`;
  heatmapCanvas.style.height = `${logicalHeight}px`;
  heatmapCanvas.width = Math.floor(logicalWidth * pixelRatio);
  heatmapCanvas.height = Math.floor(logicalHeight * pixelRatio);

  const context = heatmapCanvas.getContext("2d");
  if (!context) {
    return;
  }
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  context.clearRect(0, 0, logicalWidth, logicalHeight);
  context.fillStyle = "#fbf8f2";
  context.fillRect(0, 0, logicalWidth, logicalHeight);

  const bikesByStation = new Map();
  for (const station of stations) {
    bikesByStation.set(
      station.station_id,
      new Map(station.series.map((item) => [item.timestamp, item.num_bikes_available]))
    );
  }

  for (let row = 0; row < stations.length; row += 1) {
    const station = stations[row];
    const bikesByTimestamp = bikesByStation.get(station.station_id);
    for (let col = 0; col < timestamps.length; col += 1) {
      const timestamp = timestamps[col];
      const bikes = bikesByTimestamp?.get(timestamp);
      context.fillStyle = viridisColor(bikes, minValue, maxValue);
      context.fillRect(
        leftPadding + col * cellWidth,
        topPadding + row * cellHeight,
        cellWidth - 1,
        cellHeight - 1
      );
    }
  }

  context.fillStyle = "#405060";
  context.font = "11px Avenir Next, sans-serif";
  context.textAlign = "right";
  context.textBaseline = "middle";

  for (let row = 0; row < stations.length; row += 1) {
    const y = topPadding + row * cellHeight + cellHeight / 2;
    context.fillText(stations[row].name, leftPadding - 8, y);
  }

  context.textAlign = "center";
  context.textBaseline = "top";
  const maxLabels = 12;
  const labelStep = Math.max(1, Math.ceil(timestamps.length / maxLabels));
  for (let col = 0; col < timestamps.length; col += labelStep) {
    const x = leftPadding + col * cellWidth + cellWidth / 2;
    context.fillText(formatTimestampLabel(timestamps[col]), x, logicalHeight - 20);
  }

  context.strokeStyle = "#cbbca8";
  context.lineWidth = 1;
  context.strokeRect(
    leftPadding - 0.5,
    topPadding - 0.5,
    timestamps.length * cellWidth + 1,
    stations.length * cellHeight + 1
  );

  heatmapGeometry = {
    leftPadding,
    topPadding,
    cellWidth,
    cellHeight,
    timestamps,
    stations,
    bikesByStation,
  };
}

function computeSeriesLookup() {
  stationSeriesById = new Map();
  const values = [];
  for (const station of dailyData.stations || []) {
    const seriesMap = new Map();
    for (const item of station.series || []) {
      seriesMap.set(item.timestamp, item.num_bikes_available);
      if (Number.isFinite(item.num_bikes_available)) {
        values.push(item.num_bikes_available);
      }
    }
    stationSeriesById.set(station.station_id, seriesMap);
  }

  snapshotMinBikes = values.length > 0 ? Math.min(...values) : 0;
  snapshotMaxBikes = values.length > 0 ? Math.max(...values) : 1;
}

function getNearestSnapshotIndex(targetIndex) {
  const timestamps = dailyData.timestamps || [];
  if (timestamps.length === 0) {
    return 0;
  }
  return Math.max(0, Math.min(timestamps.length - 1, targetIndex));
}

function updateSnapshotMapAtIndex(index) {
  const timestamps = dailyData.timestamps || [];
  if (!snapshotTimeLabelEl || timestamps.length === 0) {
    return;
  }

  const nearestIndex = getNearestSnapshotIndex(index);
  const timestamp = timestamps[nearestIndex];
  const timeLabel = formatTimestampLabel(timestamp);
  snapshotTimeLabelEl.textContent = `Snapshot time: ${timeLabel} (nearest data point)`;

  let withDataCount = 0;
  for (const station of dailyData.stations || []) {
    const marker = snapshotMarkersByStationId.get(station.station_id);
    if (!marker) {
      continue;
    }

    const bikes = stationSeriesById.get(station.station_id)?.get(timestamp);
    const color = viridisColor(bikes, snapshotMinBikes, snapshotMaxBikes);
    marker.setStyle({
      fillColor: color,
      color,
      radius: 8,
      weight: 2,
      fillOpacity: 0.95,
    });

    const valueLabel = Number.isFinite(bikes) ? bikes : "n/a";
    if (Number.isFinite(bikes)) {
      withDataCount += 1;
    }
    marker.bindTooltip(`${station.name}: ${valueLabel} bikes`, {
      direction: "top",
      offset: [0, -6],
    });
  }

  if (snapshotStatusEl) {
    snapshotStatusEl.textContent =
      `Showing ${withDataCount} stations with data at ${timeLabel}.`;
  }
}

function initSnapshotMap() {
  if (!snapshotMapContainer) {
    return;
  }

  snapshotMap = L.map(snapshotMapContainer, {
    zoomControl: true,
    attributionControl: true,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(snapshotMap);

  const bounds = [];
  for (const station of dailyData.stations || []) {
    if (!Number.isFinite(station.lat) || !Number.isFinite(station.lon)) {
      continue;
    }

    const marker = L.circleMarker([station.lat, station.lon], {
      radius: 8,
      fillColor: "#21918c",
      color: "#21918c",
      weight: 2,
      fillOpacity: 0.95,
    });
    marker.addTo(snapshotMap);

    snapshotMarkersByStationId.set(station.station_id, marker);
    bounds.push([station.lat, station.lon]);
  }

  if (bounds.length === 0) {
    snapshotMap.setView([49.1193, 6.1757], 12);
  } else {
    snapshotMap.fitBounds(bounds, { padding: [20, 20] });
  }

  if (snapshotSlider) {
    const maxIndex = Math.max(0, (dailyData.timestamps || []).length - 1);
    snapshotSlider.min = "0";
    snapshotSlider.max = String(maxIndex);
    snapshotSlider.step = "1";
    snapshotSlider.value = String(maxIndex);
    snapshotSlider.addEventListener("input", (event) => {
      const nextIndex = Number.parseInt(event.target.value, 10);
      updateSnapshotMapAtIndex(nextIndex);
    });
  }

  updateSnapshotMapAtIndex((dailyData.timestamps || []).length - 1);
}

function handleHeatmapHover(event) {
  if (!heatmapGeometry || !heatmapStatusEl) {
    return;
  }

  const rect = heatmapCanvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  const col = Math.floor((x - heatmapGeometry.leftPadding) / heatmapGeometry.cellWidth);
  const row = Math.floor((y - heatmapGeometry.topPadding) / heatmapGeometry.cellHeight);

  const inBounds =
    row >= 0 &&
    row < heatmapGeometry.stations.length &&
    col >= 0 &&
    col < heatmapGeometry.timestamps.length;

  if (!inBounds) {
    heatmapStatusEl.textContent = "Hover a cell to inspect a station and snapshot value.";
    return;
  }

  const station = heatmapGeometry.stations[row];
  const timestamp = heatmapGeometry.timestamps[col];
  const bikes = heatmapGeometry.bikesByStation.get(station.station_id)?.get(timestamp);
  const bikesLabel = Number.isFinite(bikes) ? bikes : "n/a";
  heatmapStatusEl.textContent = `${station.name} at ${toLocalTime(timestamp)}: ${bikesLabel} bikes`;
}

function clearHeatmapHover() {
  if (heatmapStatusEl) {
    heatmapStatusEl.textContent = "Hover a cell to inspect a station and snapshot value.";
  }
}

function buildChart(selectedStations) {
  const timestamps = dailyData.timestamps || [];

  const datasets = selectedStations.map((station) => {
    const bikesByTimestamp = new Map(
      station.series.map((item) => [item.timestamp, item.num_bikes_available])
    );
    const color = colorForStationId(station.station_id);

    return {
      label: station.name,
      data: timestamps.map((timestamp) => ({
        x: Date.parse(timestamp),
        y: bikesByTimestamp.get(timestamp) ?? null,
      })),
      borderColor: color,
      backgroundColor: `${color}30`,
      borderWidth: 3,
      fill: false,
      tension: 0.25,
      pointRadius: 1.5,
      pointHoverRadius: 4,
      spanGaps: true,
    };
  });

  if (chart) {
    chart.destroy();
  }

  const allValues = datasets.flatMap((dataset) => dataset.data).filter((item) => Number.isFinite(item));
  const maxValue = allValues.length > 0 ? Math.max(...allValues) : 1;
  const minValue = allValues.length > 0 ? Math.min(...allValues) : 0;
  const valueRange = Math.max(1, maxValue - minValue);
  const margin = Math.ceil(valueRange * 0.2);

  chart = new Chart(chartCanvas, {
    type: "line",
    data: {
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 800,
      },
      scales: {
        x: {
          type: "linear",
          ticks: {
            maxTicksLimit: 12,
            callback: (value) => {
              const timestamp = Number(value);
              return Number.isFinite(timestamp) ? formatTimestampLabel(new Date(timestamp).toISOString()) : "";
            },
          },
          title: {
            display: true,
            text: "Time",
          },
        },
        y: {
          beginAtZero: true,
          suggestedMin: Math.max(0, minValue - margin),
          suggestedMax: maxValue + margin,
          ticks: {
            precision: 0,
          },
        },
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            title: (items) => {
              const item = items[0];
              const timestamp = item?.parsed?.x;
              return Number.isFinite(timestamp)
                ? formatTimestampLabel(new Date(timestamp).toISOString())
                : "";
            },
            label: (item) => {
              const bikes = Number.isFinite(item.parsed.y) ? item.parsed.y : "n/a";
              return `${item.dataset.label}: ${bikes} bikes`;
            },
          },
        },
      },
    },
  });
}

function setMarkerSelected(stationId, isSelected) {
  const marker = markersByStationId.get(stationId);
  if (!marker) {
    return;
  }
  const selectedColor = colorForStationId(stationId);
  marker.setStyle({
    radius: isSelected ? 10 : 7,
    fillColor: isSelected ? selectedColor : "#156f64",
    color: isSelected ? selectedColor : "#0f524a",
    fillOpacity: 0.92,
    weight: isSelected ? 3 : 2,
  });
}

function getStationById(stationId) {
  return dailyData.stations.find((item) => item.station_id === stationId);
}

function refreshSelectionView() {
  const selectedStations = Array.from(selectedStationIds)
    .map((stationId) => getStationById(stationId))
    .filter((station) => station && Array.isArray(station.series));

  if (selectedStations.length === 0) {
    if (chart) {
      chart.destroy();
      chart = null;
    }
    stationTitleEl.textContent = "Select one or more stations on the map";
    statusEl.textContent = "Click station points on the map to compare bike availability over time.";
    return;
  }

  buildChart(selectedStations);
  stationTitleEl.textContent = `${selectedStations.length} station${selectedStations.length > 1 ? "s" : ""} selected`;

  const latestSummary = selectedStations
    .map((station) => {
      const lastPoint = station.series[station.series.length - 1];
      const bikes = lastPoint?.num_bikes_available ?? "n/a";
      return `${station.name}: ${bikes}`;
    })
    .join(" | ");
  statusEl.textContent = `Latest bikes by station: ${latestSummary}`;
}

function toggleStationSelection(stationId, panTo = false) {
  if (!dailyData) {
    return;
  }

  const station = getStationById(stationId);
  if (!station) {
    statusEl.textContent = "No station data available.";
    return;
  }

  if (selectedStationIds.has(stationId)) {
    selectedStationIds.delete(stationId);
    setMarkerSelected(stationId, false);
  } else {
    selectedStationIds.add(stationId);
    setMarkerSelected(stationId, true);
  }
  refreshSelectionView();

  if (panTo && map && Number.isFinite(station.lat) && Number.isFinite(station.lon)) {
    map.panTo([station.lat, station.lon], { animate: true, duration: 0.35 });
  }
}

function initMap() {
  map = L.map(mapContainer, {
    zoomControl: true,
    attributionControl: true,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  const bounds = [];
  for (const station of dailyData.stations) {
    if (!Number.isFinite(station.lat) || !Number.isFinite(station.lon)) {
      continue;
    }

    const marker = L.circleMarker([station.lat, station.lon], {
      radius: 7,
      fillColor: "#156f64",
      color: "#0f524a",
      weight: 2,
      fillOpacity: 0.92,
    });

    marker.bindTooltip(station.name, { direction: "top", offset: [0, -6] });
    marker.on("click", () => {
      toggleStationSelection(station.station_id);
    });
    marker.addTo(map);

    markersByStationId.set(station.station_id, marker);
    bounds.push([station.lat, station.lon]);
  }

  if (bounds.length === 0) {
    map.setView([49.1193, 6.1757], 12);
    return;
  }

  map.fitBounds(bounds, { padding: [20, 20] });
}

async function loadData() {
  let response = await fetch("data/all_series.json", { cache: "no-store" });
  if (!response.ok) {
    response = await fetch("data/today_series.json", { cache: "no-store" });
  }
  if (!response.ok) {
    throw new Error("Could not load daily data file");
  }

  dailyData = await response.json();
  const stationCount = dailyData.stations.length;

  if (stationCount === 0) {
    metaEl.textContent = `No snapshots available yet for ${dailyData.date}.`;
    statusEl.textContent = "The collector will populate data every 10 minutes.";
    return;
  }

  const rangeText =
    dailyData.range_start && dailyData.range_end
      ? `${formatTimestampLabel(dailyData.range_start)} → ${formatTimestampLabel(dailyData.range_end)}`
      : dailyData.date;
  metaEl.textContent = `${rangeText} - ${dailyData.snapshot_count} snapshots - ${stationCount} stations`;

  computeSeriesLookup();
  initMap();
  toggleStationSelection(dailyData.stations[0].station_id, true);
  buildHeatmap();
  initSnapshotMap();

  heatmapCanvas.addEventListener("mousemove", handleHeatmapHover);
  heatmapCanvas.addEventListener("mouseleave", clearHeatmapHover);
}

loadData().catch((error) => {
  console.error(error);
  if (window.location.protocol === "file:") {
    statusEl.textContent =
      "Local file mode blocks data loading. Run: uv run python -m http.server --directory docs 8000, then open http://localhost:8000.";
    return;
  }

  statusEl.textContent = "Unable to load chart data. Check docs/data/today_series.json or run the collector workflow.";
});

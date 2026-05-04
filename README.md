# graoulib-app

Base project to collect and visualize Metz bike station availability from the public GBFS feed:
https://gbfs.partners.fifteen.eu/gbfs/metz/gbfs.json

## What this scaffold does

- Fetches station information + station status from GBFS.
- Stores historical snapshots every 10 minutes in `data/history/YYYY-MM-DD.ndjson`.
- Updates `data/latest_snapshot.json`.
- Builds `docs/data/all_series.json` for a static chart page.
- Includes a GitHub Actions workflow scheduled every 10 minutes.
- Serves a static chart UI from `docs/` (compatible with GitHub Pages).

## Project layout

- `src/graoulib/`: core Python package.
- `scripts/collect_snapshot.py`: fetches and stores one snapshot.
- `scripts/build_site_data.py`: creates aggregated daily chart data.
- `scripts/run_collect_loop.py`: runs the collection loop locally.
- `data/history/`: daily NDJSON historical archives.
- `docs/`: static GitHub Pages site.
- `.github/workflows/collect-data.yml`: scheduler and auto-commit pipeline.

## Local usage

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync
uv run python scripts/collect_snapshot.py
# or to run the loop locally every 10 minutes:
uv run python scripts/run_collect_loop.py
uv run python scripts/build_site_data.py
```

Open `docs/index.html` in a browser (or use a local static server).

If you open the file directly with `file://`, browsers can block JSON fetch requests. Prefer running a local server:

```bash
uv run python -m http.server --directory docs 8000
```

Then open `http://localhost:8000`.

## One-liner to build and serve

```bash
uv run python scripts/build_site_data.py && uv run python -m http.server --directory docs 8000
```

## Daily operation with uv

Use these commands when you want to collect manually:

```bash
uv run python scripts/collect_snapshot.py
uv run python scripts/build_site_data.py
```

## Testing

```bash
uv sync --group dev
uv run pytest -q
```

## GitHub Pages

This repository is now ready for GitHub-hosted automation and publication.

### 1. Push to GitHub

```bash
git add .
git commit -m "chore: setup pages and data collection"
git push origin main
```

### 2. Enable workflows and Pages

In repository settings:

1. Enable Pages.
2. Set source to `GitHub Actions`.
3. In `Actions > General`, ensure workflow permissions allow read and write access.

### What runs automatically

- `.github/workflows/collect-data.yml`: every 10 minutes, fetches a snapshot, appends history, and commits updated data files.
- `.github/workflows/deploy-pages.yml`: deploys `docs/` to GitHub Pages after pushes affecting site content.

Data is persisted in `data/history/YYYY-MM-DD.ndjson`, and the published site reads from `docs/data/`.

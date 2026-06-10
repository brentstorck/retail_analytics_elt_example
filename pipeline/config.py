"""Central configuration. Paths come from env vars (with sensible repo-relative
defaults) so the Python loader and dbt always agree on where the warehouse lives."""
from __future__ import annotations

import os
from pathlib import Path

# Repo root = parent of the `pipeline/` package.
REPO_ROOT = Path(__file__).resolve().parents[1]


def _path_from_env(var: str, default: Path) -> Path:
    raw = os.environ.get(var)
    return Path(raw).expanduser() if raw else default


# --- filesystem ----------------------------------------------------------------
DATA_DIR = _path_from_env("DATA_DIR", REPO_ROOT / "data")
EXPORT_DIR = DATA_DIR / "exports"
DBT_DIR = REPO_ROOT / "retail_dbt"

# --- warehouse -----------------------------------------------------------------
# IMPORTANT: dbt's profiles.yml reads the same DUCKDB_PATH env var.
DUCKDB_PATH = _path_from_env("DUCKDB_PATH", REPO_ROOT / "warehouse" / "retail.duckdb")

# --- source dataset ------------------------------------------------------------
# UCI Online Retail II (.xlsx, two sheets). Public, no auth. A mirror is tried if the
# primary host is unavailable.
DATASET_URL = os.environ.get(
    "DATASET_URL",
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00502/online_retail_II.xlsx",
)
DATASET_MIRRORS = [
    "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip",
]
XLSX_PATH = DATA_DIR / "online_retail_II.xlsx"

# Small committed sample of the raw data, used by CI (and quick local checks) so dbt can
# build and test fast and offline without downloading the full ~45 MB dataset.
SAMPLE_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_online_retail.csv"

# --- raw landing zone in the warehouse -----------------------------------------
RAW_SCHEMA = "raw"
RAW_TABLE = "online_retail"

# Marts exported to CSV for Hex upload / sharing.
EXPORTED_MARTS = [
    "marts.mart_revenue_daily",
    "marts.mart_revenue_monthly",
    "marts.mart_customer_cohorts",
    "marts.mart_rfm_segments",
    "marts.mart_country_performance",
    "marts.mart_product_performance",
    "marts.mart_data_quality",
]


def ensure_dirs() -> None:
    for d in (DATA_DIR, EXPORT_DIR, DUCKDB_PATH.parent):
        d.mkdir(parents=True, exist_ok=True)

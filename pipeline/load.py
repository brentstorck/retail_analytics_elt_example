"""Load: read the raw data into the DuckDB landing zone (raw.online_retail).

This is the "raw logs" layer the JD describes. Cleaning is deliberately minimal here: we
only normalize column names/types and add lineage columns. All business logic (flagging
cancellations, filtering bad lines, etc.) happens downstream in dbt, so the raw layer stays
an honest mirror of the source.

The transformation helpers (normalize_columns / coerce_types / dedupe) are pure functions
so they can be unit-tested without touching the filesystem or the warehouse (see
tests/test_pipeline.py). `load()` reads the full Excel source; `load_sample()` loads the
small committed CSV fixture and is what CI uses.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import duckdb
import pandas as pd

from . import config, extract

# Source headers (they vary slightly across sheets/exports) -> our snake_case names.
COLUMN_MAP = {
    "invoice": "invoice",
    "invoiceno": "invoice",
    "stockcode": "stock_code",
    "description": "description",
    "quantity": "quantity",
    "invoicedate": "invoice_date",
    "price": "price",
    "unitprice": "price",
    "customer id": "customer_id",
    "customerid": "customer_id",
    "country": "country",
}

RAW_COLUMNS = [
    "invoice", "stock_code", "description", "quantity", "invoice_date",
    "price", "customer_id", "country", "_source_sheet", "_loaded_at",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map source headers to snake_case names (case/space-insensitive)."""
    return df.rename(columns=lambda c: COLUMN_MAP.get(str(c).strip().lower(), str(c).strip().lower()))


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Cast columns to consistent types and clean the customer id into a string/NULL."""
    df = df.copy()
    df["invoice"] = df["invoice"].astype("string").str.strip()
    df["stock_code"] = df["stock_code"].astype("string").str.strip()
    df["description"] = df["description"].astype("string").str.strip()
    df["country"] = df["country"].astype("string").str.strip()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
    df["price"] = pd.to_numeric(df["price"], errors="coerce").astype("float64")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

    # Customer ID arrives as a float (e.g. 17850.0). Cast via nullable Int (drops the ".0")
    # then to nullable string, so missing ids become NA -> SQL NULL in the warehouse.
    df["customer_id"] = (
        pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64").astype("string")
    )
    return df


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact-duplicate raw rows (same line scanned twice)."""
    return df.drop_duplicates(
        subset=["invoice", "stock_code", "quantity", "price", "invoice_date", "customer_id"]
    )


def _read_xlsx(path: str) -> pd.DataFrame:
    """Read both sheets, tag the source sheet, and concatenate."""
    print(f"[load] reading {path} (both sheets; ~1M rows, takes a minute)")
    sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    frames = []
    for sheet_name, df in sheets.items():
        df = normalize_columns(df)
        df["_source_sheet"] = sheet_name
        frames.append(df)
        print(f"  sheet '{sheet_name}': {len(df):,} rows")
    return pd.concat(frames, ignore_index=True)


def _write_raw(df: pd.DataFrame) -> int:
    """Stamp lineage columns and (re)create raw.online_retail. Returns the row count."""
    df = df.copy()
    if "_source_sheet" not in df.columns:
        df["_source_sheet"] = "sample"
    df["_loaded_at"] = dt.datetime.now()
    df = df[RAW_COLUMNS]

    print(f"[load] writing to {config.DUCKDB_PATH} :: {config.RAW_SCHEMA}.{config.RAW_TABLE}")
    con = duckdb.connect(str(config.DUCKDB_PATH))
    try:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {config.RAW_SCHEMA}")
        con.register("incoming", df)
        con.execute(
            f"CREATE OR REPLACE TABLE {config.RAW_SCHEMA}.{config.RAW_TABLE} AS "
            f"SELECT * FROM incoming"
        )
        return con.execute(
            f"SELECT count(*) FROM {config.RAW_SCHEMA}.{config.RAW_TABLE}"
        ).fetchone()[0]
    finally:
        con.close()


def load() -> int:
    """Load the full Online Retail II dataset into DuckDB raw.online_retail."""
    config.ensure_dirs()
    path = extract.extract()

    df = _read_xlsx(path)
    df = coerce_types(df)

    before = len(df)
    df = dedupe(df)
    print(f"[load] dropped {before - len(df):,} exact-duplicate rows ({len(df):,} remain)")

    n = _write_raw(df)
    print(f"[load] done: {n:,} rows in {config.RAW_SCHEMA}.{config.RAW_TABLE}")
    return n


def load_sample(path: str | Path | None = None) -> int:
    """Load the small committed CSV fixture into raw.online_retail (used by CI)."""
    config.ensure_dirs()
    fixture = Path(path or config.SAMPLE_FIXTURE)
    print(f"[load_sample] reading fixture {fixture}")
    df = coerce_types(pd.read_csv(fixture))
    n = _write_raw(df)
    print(f"[load_sample] done: {n:,} rows in {config.RAW_SCHEMA}.{config.RAW_TABLE}")
    return n


if __name__ == "__main__":
    load()

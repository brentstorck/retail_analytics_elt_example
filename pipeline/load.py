"""Load: read the raw .xlsx into the DuckDB landing zone (raw.online_retail).

This is the "raw logs" layer the JD describes. Cleaning is deliberately minimal here —
we only normalize column names/types and add lineage columns. All business logic
(flagging cancellations, filtering bad lines, dedup decisions) happens downstream in dbt,
so the raw layer stays an honest mirror of the source.
"""
from __future__ import annotations

import datetime as dt

import duckdb
import pandas as pd

from . import config, extract

# Source headers (vary slightly across sheets) -> our snake_case names.
_COLUMN_MAP = {
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


def _read_xlsx(path: str) -> pd.DataFrame:
    """Read both sheets, tag the source sheet, and concatenate."""
    print(f"[load] reading {path} (both sheets; ~1M rows, takes a minute)")
    sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    frames = []
    for sheet_name, df in sheets.items():
        df = df.rename(columns=lambda c: _COLUMN_MAP.get(str(c).strip().lower(), str(c).strip().lower()))
        df["_source_sheet"] = sheet_name
        frames.append(df)
        print(f"  sheet '{sheet_name}': {len(df):,} rows")
    return pd.concat(frames, ignore_index=True)


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    df["invoice"] = df["invoice"].astype("string").str.strip()
    df["stock_code"] = df["stock_code"].astype("string").str.strip()
    df["description"] = df["description"].astype("string").str.strip()
    df["country"] = df["country"].astype("string").str.strip()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
    df["price"] = pd.to_numeric(df["price"], errors="coerce").astype("float64")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

    # Customer ID arrives as a float (e.g. 17850.0); keep it as a clean string id or NULL.
    cid = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")
    df["customer_id"] = [str(int(v)) if pd.notna(v) else None for v in cid]
    return df


def load() -> int:
    """Load the dataset into DuckDB raw.online_retail. Returns the row count."""
    config.ensure_dirs()
    path = extract.extract()

    df = _read_xlsx(path)
    df = _coerce_types(df)

    before = len(df)
    df = df.drop_duplicates(
        subset=["invoice", "stock_code", "quantity", "price", "invoice_date", "customer_id"]
    )
    print(f"[load] dropped {before - len(df):,} exact-duplicate rows ({len(df):,} remain)")

    # Lineage column for dbt source-freshness SLA checks.
    df["_loaded_at"] = dt.datetime.now()

    ordered = [
        "invoice", "stock_code", "description", "quantity", "invoice_date",
        "price", "customer_id", "country", "_source_sheet", "_loaded_at",
    ]
    df = df[ordered]

    print(f"[load] writing to {config.DUCKDB_PATH} :: {config.RAW_SCHEMA}.{config.RAW_TABLE}")
    con = duckdb.connect(str(config.DUCKDB_PATH))
    try:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {config.RAW_SCHEMA}")
        con.register("incoming", df)
        con.execute(
            f"CREATE OR REPLACE TABLE {config.RAW_SCHEMA}.{config.RAW_TABLE} AS "
            f"SELECT * FROM incoming"
        )
        n = con.execute(
            f"SELECT count(*) FROM {config.RAW_SCHEMA}.{config.RAW_TABLE}"
        ).fetchone()[0]
    finally:
        con.close()

    print(f"[load] done: {n:,} rows in {config.RAW_SCHEMA}.{config.RAW_TABLE}")
    return n


if __name__ == "__main__":
    load()

"""Export: write the marts to CSV so they can be uploaded to Hex (or shared).

In a cloud setup Hex connects straight to the warehouse; this export exists so the
project is fully self-serve even on Hex's free tier (upload the CSVs) and so the marts
are diff-able artifacts.
"""
from __future__ import annotations

import duckdb

from . import config


def export() -> list[str]:
    config.ensure_dirs()
    written: list[str] = []
    con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
    try:
        for fq in config.EXPORTED_MARTS:
            name = fq.split(".")[-1]
            out = config.EXPORT_DIR / f"{name}.csv"
            try:
                con.execute(f"COPY (SELECT * FROM {fq}) TO '{out.as_posix()}' (HEADER, DELIMITER ',')")
                rows = con.execute(f"SELECT count(*) FROM {fq}").fetchone()[0]
                print(f"[export] {fq:40s} -> {out}  ({rows:,} rows)")
                written.append(str(out))
            except duckdb.Error as err:
                print(f"[export] skip {fq}: {err}")
    finally:
        con.close()
    print(f"[export] wrote {len(written)} files to {config.EXPORT_DIR}")
    return written


if __name__ == "__main__":
    export()

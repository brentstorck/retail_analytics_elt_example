"""Run the full ELT pipeline end-to-end without Airflow.

    python -m pipeline.run            # extract -> load -> dbt build -> export
    python -m pipeline.run --skip-extract-load   # just rebuild dbt + export

Airflow runs these same steps as a DAG; this entrypoint keeps the project runnable on
a plain laptop (no Docker/WSL) and is what the docs use for the quickstart.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

from . import config, export, load


def _dbt_base() -> list[str]:
    """Prefer the `dbt` console script; fall back to the module entrypoint."""
    exe = shutil.which("dbt")
    if exe:
        return [exe]
    return [sys.executable, "-m", "dbt.cli.main"]


def _run_dbt(*args: str) -> None:
    env = os.environ.copy()
    env.setdefault("DUCKDB_PATH", str(config.DUCKDB_PATH))
    env["DBT_PROFILES_DIR"] = str(config.DBT_DIR)  # ship profiles.yml inside the project
    cmd = [*_dbt_base(), *args]
    print(f"\n$ {' '.join(cmd)}  (cwd={config.DBT_DIR})")
    subprocess.run(cmd, cwd=config.DBT_DIR, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the retail analytics ELT pipeline.")
    parser.add_argument(
        "--skip-extract-load",
        action="store_true",
        help="Skip extract+load and only rebuild dbt models and exports.",
    )
    args = parser.parse_args()

    print(f"DUCKDB_PATH = {config.DUCKDB_PATH}")

    if not args.skip_extract_load:
        load.load()  # load() calls extract() internally and is idempotent

    _run_dbt("deps")
    _run_dbt("seed")
    _run_dbt("build")          # models + tests in one pass
    _run_dbt("docs", "generate")

    export.export()
    print("\n[run] pipeline complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

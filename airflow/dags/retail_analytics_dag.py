"""Airflow DAG: orchestrate the retail analytics ELT on a daily schedule.

The DAG is thin on purpose: it imports the same `pipeline` functions used by
`python -m pipeline.run` and shells out to dbt. Business logic lives in the package and
the dbt project, not in the orchestrator. Task retries and SLAs encode the data-delivery
guarantees described in the job spec.

    extract -> load -> dbt deps -> (dbt seed + build) -> [freshness, docs] -> export marts
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

# The repo is mounted here by docker-compose; make the `pipeline` package importable.
PROJECT_DIR = os.environ.get("PROJECT_DIR", "/opt/airflow/project")
DBT_DIR = os.path.join(PROJECT_DIR, "retail_dbt")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# dbt needs to find the in-repo profiles.yml; everything else (DUCKDB_PATH) comes from env.
DBT_ENV = {**os.environ, "DBT_PROFILES_DIR": DBT_DIR}

default_args = {
    "owner": "brent.storck",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "sla": timedelta(hours=2),
}


def _alert_on_failure(context) -> None:
    """Hook for paging/Slack in a real deployment; logs here for the demo."""
    ti = context.get("task_instance")
    print(f"[ALERT] task '{ti.task_id}' failed in run '{context.get('run_id')}'")


@dag(
    dag_id="retail_analytics",
    description="ELT: UCI Online Retail II -> DuckDB -> dbt marts -> Hex/export",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    on_failure_callback=_alert_on_failure,
    tags=["dbt", "duckdb", "elt", "retail", "analytics-engineering"],
)
def retail_analytics():

    @task
    def extract() -> str:
        from pipeline.extract import extract as run_extract
        return run_extract()

    @task
    def load(xlsx_path: str) -> int:
        from pipeline.load import load as run_load
        return run_load()

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd '{DBT_DIR}' && dbt deps",
        env=DBT_ENV,
        append_env=True,
    )

    dbt_build = BashOperator(
        task_id="dbt_seed_and_build",
        bash_command=f"cd '{DBT_DIR}' && dbt seed && dbt build",
        env=DBT_ENV,
        append_env=True,
        sla=timedelta(hours=1),  # marts must be fresh within an hour of the run starting
    )

    dbt_freshness = BashOperator(
        task_id="dbt_source_freshness",
        bash_command=f"cd '{DBT_DIR}' && dbt source freshness",
        env=DBT_ENV,
        append_env=True,
    )

    dbt_docs = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"cd '{DBT_DIR}' && dbt docs generate",
        env=DBT_ENV,
        append_env=True,
    )

    @task
    def export_marts() -> list[str]:
        from pipeline.export import export as run_export
        return run_export()

    xlsx = extract()
    loaded = load(xlsx)
    exported = export_marts()

    loaded >> dbt_deps >> dbt_build >> [dbt_freshness, dbt_docs] >> exported


retail_analytics()

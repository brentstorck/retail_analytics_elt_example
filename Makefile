# Convenience targets. On Windows without `make`, use run.ps1 or the raw commands in README.
# All dbt targets assume DUCKDB_PATH is exported and point dbt at the in-repo profiles.yml.

DBT = cd retail_dbt && dbt

.PHONY: install extract load build test unit lint docs export run dashboard sample clean all

install:
	pip install -r requirements.txt
	$(DBT) deps

extract:
	python -m pipeline.extract

load:
	python -m pipeline.load

build:           ## run models + tests
	$(DBT) build

test:
	$(DBT) test

freshness:
	$(DBT) source freshness

docs:
	$(DBT) docs generate

export:
	python -m pipeline.export

run:             ## full pipeline, no Airflow
	python -m pipeline.run

dashboard:
	streamlit run dashboard/app.py

unit:            ## python unit tests (pytest)
	pytest

lint:            ## sql lint (informational)
	sqlfluff lint retail_dbt/models

sample:          ## load the small CI fixture instead of the full dataset
	python -c "from pipeline.load import load_sample; load_sample()"

clean:
	rm -rf retail_dbt/target retail_dbt/dbt_packages retail_dbt/logs
	rm -f warehouse/*.duckdb warehouse/*.duckdb.wal

all: install run docs

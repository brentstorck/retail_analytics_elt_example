"""Retail analytics ELT pipeline.

Pure-Python extract / load / export steps with no orchestration dependency, so the
pipeline runs on any machine (`python -m pipeline.run`) and Airflow simply calls into
these functions. Keeping orchestration out of the business logic keeps it testable.
"""

-- Singular test: a cohort can never retain more than 100% of its customers.
-- Guards the cohort math (cohort size vs. active customers).

select
    cohort_month,
    months_since_cohort,
    retention_rate
from {{ ref('mart_customer_cohorts') }}
where retention_rate > 1.0

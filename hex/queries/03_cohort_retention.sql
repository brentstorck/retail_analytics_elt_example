-- Cohort retention heatmap source.
-- In Hex: pivot with cohort_month as rows, months_since_cohort as columns,
-- retention_rate as the colored value. Capped at 18 months for readability.
select
    cohort_month,
    months_since_cohort,
    cohort_customers,
    n_active_customers,
    retention_rate
from marts.mart_customer_cohorts
where months_since_cohort between 0 and 18
order by cohort_month, months_since_cohort;

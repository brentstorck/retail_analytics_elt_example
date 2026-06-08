-- Metric mart: monthly acquisition-cohort retention.
-- For each cohort (month of first order) and each subsequent month, what share of the
-- original cohort placed an order? This is the classic retention-heatmap source table.

with orders as (

    select
        o.customer_id,
        c.cohort_month,
        cast(date_trunc('month', o.order_date) as date) as activity_month
    from {{ ref('fct_orders') }} o
    join {{ ref('dim_customers') }} c using (customer_id)
    where not o.is_cancellation

),

activity as (

    select
        cohort_month,
        activity_month,
        (extract(year from activity_month) - extract(year from cohort_month)) * 12
            + (extract(month from activity_month) - extract(month from cohort_month)) as months_since_cohort,
        count(distinct customer_id)                                                   as n_active_customers
    from orders
    group by cohort_month, activity_month

),

cohort_size as (

    select cohort_month, count(distinct customer_id) as cohort_customers
    from {{ ref('dim_customers') }}
    group by cohort_month

)

select
    a.cohort_month,
    s.cohort_customers,
    a.months_since_cohort,
    a.activity_month,
    a.n_active_customers,
    round(a.n_active_customers::double / nullif(s.cohort_customers, 0), 4) as retention_rate
from activity a
join cohort_size s using (cohort_month)
order by a.cohort_month, a.months_since_cohort

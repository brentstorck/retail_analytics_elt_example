-- Analysis (compiled by dbt, not materialized): how concentrated is revenue?
-- Answers "what share of revenue comes from the top 10% of customers?", a question a
-- GTM lead asks. Run `dbt compile` and copy the compiled SQL, or paste into Hex.

with ranked as (

    select
        customer_id,
        lifetime_revenue,
        ntile(10) over (order by lifetime_revenue desc) as revenue_decile
    from {{ ref('dim_customers') }}

)

select
    revenue_decile,
    count(*)                                                       as n_customers,
    round(sum(lifetime_revenue))                                   as revenue,
    round(100.0 * sum(lifetime_revenue) / sum(sum(lifetime_revenue)) over (), 2) as pct_of_total_revenue
from ranked
group by revenue_decile
order by revenue_decile

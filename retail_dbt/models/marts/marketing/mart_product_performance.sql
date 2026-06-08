-- Metric mart: product leaderboard by net revenue, with return rate and revenue share.

with products as (

    select * from {{ ref('dim_products') }}
    where total_revenue > 0

)

select
    stock_code,
    description,
    n_orders,
    units_sold,
    units_returned,
    total_revenue,
    return_rate,
    row_number() over (order by total_revenue desc)                  as revenue_rank,
    round(total_revenue / sum(total_revenue) over () * 100, 2)       as revenue_share_pct
from products
order by total_revenue desc

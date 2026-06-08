-- Top products by net revenue, with return rate. Table or horizontal bar.
select
    revenue_rank,
    stock_code,
    description,
    units_sold,
    total_revenue,
    revenue_share_pct,
    return_rate
from marts.mart_product_performance
order by revenue_rank
limit 25;

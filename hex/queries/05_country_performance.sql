-- Geography: revenue by region and country.
-- Chart A (map/bar): revenue by country. Chart B: revenue rolled up by region.
select
    region,
    country,
    n_customers,
    n_orders,
    revenue,
    avg_order_value,
    revenue_share_pct
from marts.mart_country_performance
order by revenue desc;

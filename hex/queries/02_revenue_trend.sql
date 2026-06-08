-- Monthly revenue trend with growth and customer mix.
-- Chart: bars = revenue, line = revenue_mom_pct; or stacked new vs returning customers.
select
    month,
    revenue,
    revenue_mom_pct,
    n_new_customers,
    n_returning_customers,
    avg_order_value
from marts.mart_revenue_monthly
order by month;

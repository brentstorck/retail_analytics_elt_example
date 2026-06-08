-- Headline KPI tiles. One row of company-wide totals.
select
    round(sum(revenue))                                   as total_net_revenue,
    sum(n_orders)                                         as total_orders,
    sum(n_new_customers)                                  as total_new_customers,
    round(sum(revenue) / nullif(sum(n_orders), 0), 2)     as avg_order_value
from marts.mart_revenue_daily;

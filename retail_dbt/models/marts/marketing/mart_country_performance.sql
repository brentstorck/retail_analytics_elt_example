-- Metric mart: revenue and customers by country, enriched with GTM region from the seed.

with orders as (

    select * from {{ ref('fct_orders') }}
    where not is_cancellation

),

agg as (

    select
        country,
        count(distinct customer_id)                                  as n_customers,
        count(distinct invoice_id)                                   as n_orders,
        round(sum(order_revenue), 2)                                 as revenue,
        round(sum(order_revenue) / nullif(count(distinct invoice_id), 0), 2) as avg_order_value
    from orders
    group by country

)

select
    a.country,
    coalesce(r.region, 'Other')                                      as region,
    a.n_customers,
    a.n_orders,
    a.revenue,
    a.avg_order_value,
    round(a.revenue / sum(a.revenue) over () * 100, 2)               as revenue_share_pct
from agg a
left join {{ ref('country_region') }} r
    on lower(trim(a.country)) = lower(trim(r.country))
order by a.revenue desc

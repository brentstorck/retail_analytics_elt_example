-- Metric mart: RFM (Recency, Frequency, Monetary) segmentation, one row per customer.
-- Each dimension is scored 1-5 by quintile; scores combine into actionable segments that
-- a GTM/CRM team uses for targeting and lifecycle campaigns.

with base as (

    select
        customer_id,
        country,
        recency_days,
        lifetime_orders   as frequency,
        lifetime_revenue  as monetary
    from {{ ref('dim_customers') }}

),

scored as (

    select
        *,
        -- lower recency_days = more recent = better, so invert the quintile
        6 - ntile(5) over (order by recency_days asc) as r_score,
        ntile(5)     over (order by frequency   asc) as f_score,
        ntile(5)     over (order by monetary    asc) as m_score
    from base

)

select
    customer_id,
    country,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    r_score + f_score + m_score as rfm_total,
    case
        when r_score >= 4 and f_score >= 4 then 'Champions'
        when r_score >= 3 and f_score >= 3 then 'Loyal Customers'
        when r_score >= 4 and f_score <= 2 then 'New / Promising'
        when r_score = 3  and f_score <= 2 then 'Potential Loyalists'
        when r_score = 2  and f_score >= 3 then 'At Risk'
        when r_score = 1  and f_score >= 4 then 'Cannot Lose Them'
        when r_score <= 2 and f_score <= 2 then 'Hibernating / Lost'
        else 'Needs Attention'
    end as rfm_segment
from scored

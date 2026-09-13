with base as (
    select
        oi.order_id,
        oi.quantity,
        oi.unit_price,
        oi.date_key,
        p.category_name,
        o.location_key
    from {{ ref('stg_order_items') }} oi
    left join {{ ref('stg_products') }} p on oi.product_key = p.product_key
    left join {{ ref('stg_orders') }} o on oi.order_id = o.order_id
),

enriched as (
    select
        d.full_date as date,
        l.country,
        b.category_name as category,
        b.order_id,
        b.quantity,
        b.unit_price
    from base b
    left join {{ ref('stg_dates') }} d on b.date_key = d.date_key
    left join {{ ref('stg_locations') }} l on b.location_key = l.location_key
)

select
    date,
    country,
    category,
    sum(quantity * unit_price) as revenue,
    count(distinct order_id) as orders,
    sum(quantity) as units_sold,
    round(sum(quantity * unit_price) / nullif(count(distinct order_id), 0), 2) as average_order_value
from enriched
group by date, country, category
order by date, country, category
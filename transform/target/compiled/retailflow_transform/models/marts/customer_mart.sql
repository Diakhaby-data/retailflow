with orders as (
    select
        o.customer_key,
        o.order_id,
        o.total_amount,
        d.full_date as order_date
    from "retailflow"."staging"."stg_orders" o
    left join "retailflow"."staging"."stg_dates" d on o.date_key = d.date_key
),

orders_agg as (
    select
        customer_key,
        count(order_id) as orders_count,
        sum(total_amount) as total_revenue,
        max(order_date) as last_order_date
    from orders
    group by customer_key
)

select
    c.customer_id,
    coalesce(a.orders_count, 0) as orders_count,
    coalesce(a.total_revenue, 0) as total_revenue,
    case
        when a.orders_count > 0 then a.total_revenue / a.orders_count
        else 0
    end as average_order_value,
    a.last_order_date,
    c.customer_segment
from "retailflow"."staging"."stg_customers" c
left join orders_agg a on c.customer_key = a.customer_key
select
    order_key,
    order_id,
    customer_key,
    date_key,
    location_key,
    order_status,
    payment_method,
    total_amount
from "retailflow"."dwh"."fact_orders"
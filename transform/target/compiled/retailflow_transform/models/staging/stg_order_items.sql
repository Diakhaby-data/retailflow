select
    order_item_key,
    order_item_id,
    order_id,
    product_key,
    customer_key,
    date_key,
    quantity,
    unit_price,
    discount
from "retailflow"."dwh"."fact_order_items"
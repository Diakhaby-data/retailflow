select
    customer_key,
    customer_id,
    first_name,
    last_name,
    email,
    country,
    city,
    signup_date,
    customer_segment
from {{ source('dwh', 'dim_customer') }}
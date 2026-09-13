select
    location_key,
    country
from {{ source('dwh', 'dim_location') }}

    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        stock_status as value_field,
        count(*) as n_records

    from "retailflow"."marts"."inventory_mart"
    group by stock_status

)

select *
from all_values
where value_field not in (
    'ok','low_stock','out_of_stock'
)



  
  
      
    ) dbt_internal_test
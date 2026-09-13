
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select category
from "retailflow"."marts"."sales_mart"
where category is null



  
  
      
    ) dbt_internal_test
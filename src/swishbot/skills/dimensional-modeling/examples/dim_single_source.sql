-- dim_products.sql
-- Single-source dimension with hash surrogate key
-- Unknown member row injected via macro in the source CTE
-- Grain: one row per product (current state) + one unknown member

{%- set column_names = dbt_utils.get_filtered_columns_in_relation(
    from=ref('stg_shopify__products'), except=[]
) %}

with

products as (
    {{ add_unknown_member_row('stg_shopify__products') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['product_id']) }} as product_key,
        {{ dbt_utils.star(from=ref('stg_shopify__products'), relation_alias='products', except=[]) }},
        {{ dbt_utils.generate_surrogate_key(column_names) }} as hash_diff
    from products
    where valid_to is null
)

select * from final

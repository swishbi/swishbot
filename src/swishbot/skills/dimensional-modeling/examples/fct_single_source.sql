-- fct_orders.sql
-- Single-source fact table with surrogate foreign keys to dimensions
-- NULL dimension FKs coalesce to the unknown member's surrogate key
-- Grain: one row per order

with

orders as (
    select * from {{ ref('stg_jaffle_shop__orders') }}
),

customers as (
    select * from {{ ref('dim_customers') }}
),

products as (
    select * from {{ ref('dim_products') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['orders.order_id']) }} as order_key,
        coalesce(
            customers.customer_key,
            {{ dbt_utils.generate_surrogate_key([dbt.string_literal(var('unknown_member_label', '*Unknown*'))]) }}
        ) as customer_key,
        coalesce(
            products.product_key,
            {{ dbt_utils.generate_surrogate_key([dbt.string_literal(var('unknown_member_label', '*Unknown*'))]) }}
        ) as product_key,
        orders.order_id,
        orders.order_date,
        orders.quantity,
        orders.unit_price,
        orders.quantity * orders.unit_price as total_amount,
        orders.status
    from orders
    left join customers
        on orders.customer_id = customers.customer_id
    left join products
        on orders.product_id = products.product_id
)

select * from final

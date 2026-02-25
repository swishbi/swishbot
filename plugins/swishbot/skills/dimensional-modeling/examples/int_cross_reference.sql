-- int_customers_cross_referenced.sql
-- Cross-system entity cross-reference using system foreign keys
-- ERP stores crm_customer_id via nightly integration sync
-- Grain: one row per unique customer across both systems

with

crm_customers as (
    select * from {{ ref('stg_crm__customers') }}
),

erp_customers as (
    select * from {{ ref('stg_erp__customers') }}
),

-- Start from the system cross-reference that already exists:
-- the ERP stores the CRM's customer_id via integration
matched as (
    select
        crm.crm_customer_id,
        erp.erp_customer_id,
        crm.email,
        {{ dbt_utils.generate_surrogate_key(['crm.crm_customer_id']) }} as customer_key
    from crm_customers as crm
    inner join erp_customers as erp
        on crm.crm_customer_id = erp.crm_customer_id
),

-- CRM-only customers (no ERP record yet)
crm_only as (
    select
        crm.crm_customer_id,
        cast(null as {{ dbt.type_string() }}) as erp_customer_id,
        crm.email,
        {{ dbt_utils.generate_surrogate_key(['crm.crm_customer_id']) }} as customer_key
    from crm_customers as crm
    where not exists (
        select 1 from erp_customers as erp
        where crm.crm_customer_id = erp.crm_customer_id
    )
),

-- ERP-only customers (no CRM link — the cross-reference gap)
erp_only as (
    select
        cast(null as {{ dbt.type_string() }}) as crm_customer_id,
        erp.erp_customer_id,
        erp.email,
        {{ dbt_utils.generate_surrogate_key(['erp.erp_customer_id']) }} as customer_key
    from erp_customers as erp
    where erp.crm_customer_id is null
)

select * from matched
union all
select * from crm_only
union all
select * from erp_only

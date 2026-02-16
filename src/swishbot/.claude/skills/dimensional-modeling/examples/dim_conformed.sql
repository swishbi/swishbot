-- dim_customers.sql
-- Conformed dimension from CRM and ERP sources with survivorship rules
-- Uses the cross-reference model to align customer records across systems
-- Grain: one row per conformed customer

with

xref as (
    select * from {{ ref('int_customers_cross_referenced') }}
),

crm_customers as (
    select * from {{ ref('stg_crm__customers') }}
),

erp_customers as (
    select * from {{ ref('stg_erp__customers') }}
),

final as (
    select
        xref.customer_key,
        xref.email,

        -- Survivorship: CRM wins for name (entered by sales reps)
        coalesce(crm.first_name, erp.first_name) as first_name,
        coalesce(crm.last_name, erp.last_name) as last_name,

        -- Survivorship: ERP wins for address (verified for invoicing/shipping)
        coalesce(erp.address_line_1, crm.address_line_1) as address_line_1,
        coalesce(erp.city, crm.city) as city,
        coalesce(erp.state, crm.state) as state,

        -- Survivorship: most recent wins for phone
        case
            when crm.updated_at >= erp.updated_at then crm.phone
            else erp.phone
        end as phone,

        -- Preserve source keys for traceability
        xref.crm_customer_id as source_crm_id,
        xref.erp_customer_id as source_erp_id,

        -- Flag linkage status for data quality monitoring
        case
            when xref.crm_customer_id is not null and xref.erp_customer_id is not null then 'linked'
            when xref.crm_customer_id is not null then 'crm_only'
            else 'erp_only'
        end as linkage_status
    from xref
    left join crm_customers as crm
        on xref.crm_customer_id = crm.crm_customer_id
    left join erp_customers as erp
        on xref.erp_customer_id = erp.erp_customer_id
)

select * from final

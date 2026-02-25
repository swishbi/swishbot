/*
    Example Staging Model - Full Convention

    Demonstrates the complete staging pattern including:
    - Column casting with dbt type macros
    - Column grouping and ordering
    - camelCase to snake_case conversion

    This example is loader-agnostic. Add loader metadata
    columns (e.g., _dlt_id, _fivetran_synced) as the last
    section based on your ingestion tool.
*/
with source as (
    select * from {{ source('source_name', 'entities') }}
),
renamed as (
    select
        -- primary key
        id as entity_id,
        type,

        -- identifiable info (ungrouped)
        cast(name as {{ type_string() }}) as entity_name,
        cast(status as {{ type_string() }}) as status,

        -- relationships
        cast(account_id as {{ type_int() }}) as account_id,

        -- strings
        cast(external_id as {{ type_string() }}) as external_id,
        cast(street_address as {{ type_string() }}) as street_address,
        cast(locality as {{ type_string() }}) as locality,
        cast(region as {{ type_string() }}) as region,
        cast(postal_code as {{ type_string() }}) as postal_code,

        -- integers
        cast(item_count as {{ type_int() }}) as item_count,

        -- numerics
        cast(rate as {{ type_numeric() }}) as rate,
        cast(latitude as {{ type_numeric() }}) as latitude,
        cast(longitude as {{ type_numeric() }}) as longitude,

        -- booleans
        cast(is_active as {{ type_boolean() }}) as is_active,

        -- dates
        cast(invoice_date as date) as invoice_date,

        -- timestamps
        cast(recent_activity as {{ type_timestamp() }}) as recent_activity_at,
        cast(created_at as {{ type_timestamp() }}) as created_at,
        cast(updated_at as {{ type_timestamp() }}) as updated_at,
        cast(deleted_at as {{ type_timestamp() }}) as deleted_at,

        -- nested objects
        custom as custom,
        options as options

        -- loader metadata
        -- Add loader-specific columns here, e.g.:
        -- _dlt_id, _dlt_load_id (dlt)
        -- _fivetran_synced, _fivetran_deleted (Fivetran)
        -- _airbyte_raw_id, _airbyte_extracted_at (Airbyte)

    from source
)
select * from renamed

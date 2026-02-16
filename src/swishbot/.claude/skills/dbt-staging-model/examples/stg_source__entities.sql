/*
    Example Staging Model

    Demonstrates the complete staging model pattern including:
    - Column casting with dbt type macros
    - Column grouping and ordering
    - camelCase to snake_case conversion

    This example is loader-agnostic. Add loader metadata
    columns (e.g., _dlt_id, _fivetran_synced) as the last
    section based on your ingestion tool.
*/
with source as (
    select * from {{ source('source_name', 'table_name') }}
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
        cast(subpremise as {{ type_string() }}) as subpremise,
        cast(locality as {{ type_string() }}) as locality,
        cast(region as {{ type_string() }}) as region,
        cast(postal_code as {{ type_string() }}) as postal_code,
        cast(county as {{ type_string() }}) as county,
        cast(country as {{ type_string() }}) as country,
        cast(place_id as {{ type_string() }}) as place_id,
        cast(timezone as {{ type_string() }}) as timezone,
        cast(website as {{ type_string() }}) as website,

        -- integers
        cast(import_id as {{ type_int() }}) as import_id,
        cast(item_count as {{ type_int() }}) as item_count,

        -- numerics
        cast(rate as {{ type_numeric() }}) as rate,
        cast(latitude as {{ type_numeric() }}) as latitude,
        cast(longitude as {{ type_numeric() }}) as longitude,

        -- timestamps
        cast(recent_activity as {{ type_timestamp() }}) as recent_activity_at,
        cast(created_at as {{ type_timestamp() }}) as created_at,
        cast(updated_at as {{ type_timestamp() }}) as updated_at,
        cast(deleted_at as {{ type_timestamp() }}) as deleted_at,

        -- nested objects
        custom as custom,
        custom_with_labels as custom_with_labels,
        options as options

        -- loader metadata
        -- Add loader-specific columns here, e.g.:
        -- _dlt_id, _dlt_load_id (dlt)
        -- _fivetran_synced, _fivetran_deleted (Fivetran)
        -- _airbyte_raw_id, _airbyte_extracted_at (Airbyte)

    from source
)
select * from renamed

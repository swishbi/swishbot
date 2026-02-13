/*
    Example Staging Model - Full Convention

    Demonstrates the complete staging pattern including:
    - JSON attribute expansion with type casting
    - Column grouping and ordering
    - SCD2-aware dlt metadata handling

    Source JSON example:
    {
      "accountId": 12345,
      "name": "Example Entity",
      "type": "EntityType",
      "externalId": "EXT-001",
      "status": "Active",
      "rate": "0.0500",
      "itemCount": 10,
      "streetAddress": "123 Main St",
      "locality": "Springfield",
      "region": "IL",
      "postalCode": "62701",
      "latitude": 39.7817,
      "longitude": -89.6501,
      "isActive": true,
      "invoiceDate": "2025-08-22",
      "options": { "settingA": true },
      "custom": { "customField": "value" },
      "recentActivity": "2025-09-04T19:29:47+00:00",
      "createdAt": "2025-08-22T00:24:14+00:00",
      "updatedAt": "2025-09-04T19:29:47+00:00",
      "deletedAt": null
    }
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
        cast(attributes:name as {{ type_string() }}) as entity_name,
        cast(attributes:status as {{ type_string() }}) as status,

        -- relationships
        cast(attributes:accountId as {{ type_int() }}) as account_id,

        -- strings
        cast(attributes:externalId as {{ type_string() }}) as external_id,
        cast(attributes:streetAddress as {{ type_string() }}) as street_address,
        cast(attributes:locality as {{ type_string() }}) as locality,
        cast(attributes:region as {{ type_string() }}) as region,
        cast(attributes:postalCode as {{ type_string() }}) as postal_code,

        -- integers
        cast(attributes:itemCount as {{ type_int() }}) as item_count,

        -- numerics
        cast(attributes:rate as {{ type_numeric() }}) as rate,
        cast(attributes:latitude as {{ type_numeric() }}) as latitude,
        cast(attributes:longitude as {{ type_numeric() }}) as longitude,

        -- booleans
        cast(attributes:isActive as {{ type_boolean() }}) as is_active,

        -- dates
        cast(attributes:invoiceDate as date) as invoice_date,

        -- timestamps
        cast(attributes:recentActivity as {{ type_timestamp() }}) as recent_activity_at,
        cast(attributes:createdAt as {{ type_timestamp() }}) as created_at,
        cast(attributes:updatedAt as {{ type_timestamp() }}) as updated_at,
        cast(attributes:deletedAt as {{ type_timestamp() }}) as deleted_at,

        -- nested objects
        attributes:custom as custom,
        attributes:options as options,

        -- dlt metadata
        _dlt_id,
        _dlt_load_id,
        {%- if var('source_name_scd2_enabled', false) or ('scd2' in (env_var('SOURCES__SOURCE_NAME_PIPELINE__WRITE_DISPOSITION', '') | lower)) %}
        _dlt_valid_from,
        _dlt_valid_to,
        row_number() over (partition by id order by _dlt_valid_from) as _dlt_version,
        {%- endif %}
        'source_name' as _dlt_source

    from source
    {%- if var('source_name_scd2_enabled', false) or ('scd2' in (env_var('SOURCES__SOURCE_NAME_PIPELINE__WRITE_DISPOSITION', '') | lower)) %}
    where _dlt_valid_to is null
    {%- endif %}
)
select * from renamed

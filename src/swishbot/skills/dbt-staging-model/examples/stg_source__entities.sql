/*
    Example Staging Model

    Demonstrates the complete staging model pattern including:
    - JSON attribute expansion with type casting
    - Column grouping and ordering
    - SCD2-aware dlt metadata handling

    Source JSON example:
    {
      "accountId": 12345,
      "name": "Example Entity",
      "type": "EntityType",
      "externalId": "EXT-001",
      "importId": null,
      "status": "Active",
      "rate": "0.0500",
      "itemCount": 10,
      "streetAddress": "123 Main St",
      "subpremise": "Suite 100",
      "locality": "Springfield",
      "region": "IL",
      "postalCode": "62701",
      "county": "Sangamon County",
      "country": "US",
      "latitude": 39.7817,
      "longitude": -89.6501,
      "placeId": "ChIJ-abc123",
      "timezone": "America/Chicago",
      "website": "https://example.com",
      "custom": { "customField": "value" },
      "customWithLabels": { "Custom Field": "value" },
      "options": { "settingA": true, "settingB": false },
      "recentActivity": "2025-09-04T19:29:47+00:00",
      "createdAt": "2025-08-22T00:24:14+00:00",
      "updatedAt": "2025-09-04T19:29:47+00:00",
      "deletedAt": null
    }
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
        cast(attributes:name as {{ type_string() }}) as entity_name,
        cast(attributes:type as {{ type_string() }}) as entity_type,
        cast(attributes:status as {{ type_string() }}) as status,

        -- relationships
        cast(attributes:accountId as {{ type_int() }}) as account_id,

        -- strings
        cast(attributes:externalId as {{ type_string() }}) as external_id,
        cast(attributes:streetAddress as {{ type_string() }}) as street_address,
        cast(attributes:subpremise as {{ type_string() }}) as subpremise,
        cast(attributes:locality as {{ type_string() }}) as locality,
        cast(attributes:region as {{ type_string() }}) as region,
        cast(attributes:postalCode as {{ type_string() }}) as postal_code,
        cast(attributes:county as {{ type_string() }}) as county,
        cast(attributes:country as {{ type_string() }}) as country,
        cast(attributes:placeId as {{ type_string() }}) as place_id,
        cast(attributes:timezone as {{ type_string() }}) as timezone,
        cast(attributes:website as {{ type_string() }}) as website,

        -- integers
        cast(attributes:importId as {{ type_int() }}) as import_id,
        cast(attributes:itemCount as {{ type_int() }}) as item_count,

        -- numerics
        cast(attributes:rate as {{ type_numeric() }}) as rate,
        cast(attributes:latitude as {{ type_numeric() }}) as latitude,
        cast(attributes:longitude as {{ type_numeric() }}) as longitude,

        -- timestamps
        cast(attributes:recentActivity as {{ type_timestamp() }}) as recent_activity_at,
        cast(attributes:createdAt as {{ type_timestamp() }}) as created_at,
        cast(attributes:updatedAt as {{ type_timestamp() }}) as updated_at,
        cast(attributes:deletedAt as {{ type_timestamp() }}) as deleted_at,

        -- nested objects
        attributes:custom as custom,
        attributes:customWithLabels as custom_with_labels,
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

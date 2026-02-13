---
name: dbt-staging-model
description: "Conventions for writing a dbt staging model SQL file. Covers SQL structure, column casting, naming, ordering, and dlt metadata handling."
---

# dbt-staging-model

Conventions for writing a dbt staging model SQL file. Covers SQL structure, column casting, naming, ordering, and dlt metadata handling.

## Usage

When creating or updating a staging model, first inspect the source data to understand its structure. Run the `get_source_sample` macro to retrieve sample data from the source table:

```bash
cd transformation && dbt --quiet run-operation get_source_sample --args '{"source_name": "<source_name>", "table_name": "<table_name>"}'
```

This returns a dictionary where keys are column names (uppercase) and values are lists of sample data (up to 500 rows). Use the results to identify JSON field names, determine correct data types, and spot nested objects that should remain uncast.

If sample data is not available (e.g., no Snowflake connection), you can alternatively provide a sample JSON payload from the `attributes` column (or equivalent nested JSON column). Claude will produce a staging model following project conventions.

## Instructions

### SQL Structure

Every staging model follows this CTE pattern:

```sql
with source as (
    select * from {{ source('<source_name>', '<table_name>') }}
),
renamed as (
    select
        -- primary key
        id as <entity>_id,
        type,

        -- expanded attributes columns (see Column Ordering below) --

        -- dlt metadata
        _dlt_id,
        _dlt_load_id,
        {%- if var('<source_name>_scd2_enabled', false) or ('scd2' in (env_var('SOURCES__<SOURCE_NAME_UPPER>_PIPELINE__WRITE_DISPOSITION', '') | lower)) %}
        _dlt_valid_from,
        _dlt_valid_to,
        row_number() over (partition by id order by _dlt_valid_from) as _dlt_version,
        {%- endif %}
        '<source_name>' as _dlt_source

    from source
    {%- if var('<source_name>_scd2_enabled', false) or ('scd2' in (env_var('SOURCES__<SOURCE_NAME_UPPER>_PIPELINE__WRITE_DISPOSITION', '') | lower)) %}
    where _dlt_valid_to is null
    {%- endif %}
)
select * from renamed
```

Replace `<SOURCE_NAME_UPPER>` with the uppercase version (e.g., `centerpoint` -> `CENTERPOINT`).

### Column Casting Rules

Use dbt type macros for casting. Use Snowflake variant syntax (`json_column:fieldName`) to access JSON fields.

| JSON Type | dbt Macro | Example |
|-----------|-----------|---------|
| String | `{{ type_string() }}` | `cast(attributes:name as {{ type_string() }}) as entity_name` |
| Integer | `{{ type_int() }}` | `cast(attributes:accountId as {{ type_int() }}) as account_id` |
| Decimal/Float | `{{ type_numeric() }}` | `cast(attributes:amount as {{ type_numeric() }}) as amount` |
| Timestamp (ISO) | `{{ type_timestamp() }}` | `cast(attributes:createdAt as {{ type_timestamp() }}) as created_at` |
| Date | `date` | `cast(attributes:invoiceDate as date) as invoice_date` |
| Boolean | `{{ type_boolean() }}` | `cast(attributes:isActive as {{ type_boolean() }}) as is_active` |
| Nested Object | No cast | `attributes:options as options` |

Replace `attributes` with the actual JSON column name (e.g., `data`, `payload`, `properties`).

### Naming Conventions

- Convert camelCase to snake_case: `createdAt` -> `created_at`
- Use `_id` suffix for IDs: `companyId` -> `company_id`
- Use `_at` suffix for timestamps: `createdAt` -> `created_at`, `recentActivity` -> `recent_activity_at`
- Prefix entity-specific fields: `name` -> `entity_name` (e.g., `budget_name`, `company_name`)
- Use `is_` prefix for booleans: `isActive` -> `is_active`
- Keep nested objects as-is or use snake_case: `customWithLabels` -> `custom_with_labels`

### Column Ordering

Group columns in this order with section comments:

1. **Primary key** - `id as <entity>_id`, `type`
2. **Identifiable info** (ungrouped) - fields that identify the entity: `name`, `description`, `status`, `domain`, etc.
3. **Relationships** - foreign key IDs grouped together: `profile_id`, `company_id`, `property_id`, etc.
4. **Strings** - remaining string fields
5. **Integers** - non-FK integer fields
6. **Numerics** - decimal/float fields: `cost`, `price`, `total`, etc.
7. **Booleans** - boolean fields
8. **Dates** - date-only fields
9. **Timestamps** - entity-specific first, then standard `created_at`, `updated_at`, `deleted_at` last
10. **Nested objects** - JSON objects/arrays without casting
11. **dlt metadata** - `_dlt_id`, `_dlt_load_id`, SCD2 columns, `_dlt_source`

Example section comments:
```sql
-- primary key
-- identifiable info (ungrouped)
-- relationships
-- strings
-- integers
-- numerics
-- booleans
-- dates
-- timestamps
-- nested objects
-- dlt metadata
```

### Standard Timestamp Fields

Always include these at the end of the timestamps section (before nested objects), if they exist in the source data:
```sql
cast(attributes:createdAt as {{ type_timestamp() }}) as created_at,
cast(attributes:updatedAt as {{ type_timestamp() }}) as updated_at,
cast(attributes:deletedAt as {{ type_timestamp() }}) as deleted_at,
```

### Nested Objects

Leave nested objects (arrays or objects) without casting. Place at the end before dlt metadata:
```sql
attributes:custom as custom,
attributes:customWithLabels as custom_with_labels,
attributes:options as options,
```

### dlt Metadata Block

Always include these columns at the end of the select, after nested objects:
- `_dlt_id` - unique row identifier
- `_dlt_load_id` - load batch identifier
- SCD2 columns (conditional) - `_dlt_valid_from`, `_dlt_valid_to`, `_dlt_version`
- `'<source_name>' as _dlt_source` - literal source name string

The SCD2 block and `where` clause use a dual check pattern:
```sql
{%- if var('<source_name>_scd2_enabled', false) or ('scd2' in (env_var('SOURCES__<SOURCE_NAME_UPPER>_PIPELINE__WRITE_DISPOSITION', '') | lower)) %}
```

This allows SCD2 to be enabled via either a dbt var or an environment variable.

### Quick Example

Given this JSON from the `attributes` column:
```json
{
  "accountId": 555078,
  "name": "Example Company",
  "closeRate": "0.0000",
  "isActive": true,
  "options": { "setting": true },
  "createdAt": "2025-08-22T00:24:14+00:00"
}
```

Transform to:
```sql
-- identifiable info (ungrouped)
cast(attributes:name as {{ type_string() }}) as company_name,

-- relationships
cast(attributes:accountId as {{ type_int() }}) as account_id,

-- numerics
cast(attributes:closeRate as {{ type_numeric() }}) as close_rate,

-- booleans
cast(attributes:isActive as {{ type_boolean() }}) as is_active,

-- timestamps
cast(attributes:createdAt as {{ type_timestamp() }}) as created_at,

-- nested objects
attributes:options as options,
```

### Full Example

See [examples/stg_source__entities.sql](examples/stg_source__entities.sql) for a complete staging model with all column groups.

## Related Skills

- **[dbt-style](../dbt-style/SKILL.md)** — Foundational naming, SQL style, and structure conventions
- **[dbt-staging](../dbt-staging/SKILL.md)** — Full staging workflow (Step 1-11) that uses this skill for model creation
- **[dbt-mcp](../dbt-mcp/SKILL.md)** — Use `compile` to verify Jinja rendering, `show` to preview results

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

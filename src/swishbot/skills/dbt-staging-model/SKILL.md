---
name: dbt-staging-model
description: "Conventions for writing a dbt staging model SQL file. Covers SQL structure, column casting, naming, ordering, and metadata handling."
---

# dbt-staging-model

Conventions for writing a dbt staging model SQL file. Covers SQL structure, column casting, naming, ordering, and metadata handling.

## Usage

When creating or updating a staging model, first inspect the source data to understand its structure. Use the dbt MCP **`show`** tool to preview source data:

```sql
select * from {{ source('<source_name>', '<table_name>') }} limit 10
```

Use the results to identify column types, JSON field names, nested structures, and data types. For nested/variant columns, inspect them individually:

```sql
select <nested_column> from {{ source('<source_name>', '<table_name>') }} limit 10
```

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

        -- expanded columns (see Column Ordering below) --

        -- loader metadata
        ...

    from source
)
select * from renamed
```

The `source` CTE selects from the raw source. The `renamed` CTE applies all casting, renaming, and ordering. The final select is always `select * from renamed`.

### Column Casting Rules

Use dbt type macros for casting. Access JSON/variant fields using your warehouse's native syntax (see [dbt-staging](../dbt-staging/SKILL.md) for warehouse-specific syntax).

| Data Type | dbt Macro | Example |
|-----------|-----------|---------|
| String | `{{ type_string() }}` | `cast(name as {{ type_string() }}) as entity_name` |
| Integer | `{{ type_int() }}` | `cast(account_id as {{ type_int() }}) as account_id` |
| Decimal/Float | `{{ type_numeric() }}` | `cast(amount as {{ type_numeric() }}) as amount` |
| Timestamp (ISO) | `{{ type_timestamp() }}` | `cast(created_at as {{ type_timestamp() }}) as created_at` |
| Date | `date` | `cast(invoice_date as date) as invoice_date` |
| Boolean | `{{ type_boolean() }}` | `cast(is_active as {{ type_boolean() }}) as is_active` |
| Nested Object | No cast | `options as options` |

### Naming Conventions

- Convert camelCase to snake_case: `createdAt` -> `created_at`
- Use `_id` suffix for IDs: `companyId` -> `company_id`
- Use `_at` suffix for timestamps: `createdAt` -> `created_at`, `recentActivity` -> `recent_activity_at`
- Prefix entity-specific fields: `name` -> `entity_name` (e.g., `budget_name`, `company_name`)
- Use `is_` prefix for booleans: `isActive` -> `is_active`
- Keep nested objects as-is or use snake_case: `customWithLabels` -> `custom_with_labels`

### Column Ordering

Group columns in this order with section comments:

1. **Primary key** — `id as <entity>_id`, `type`
2. **Identifiable info** (ungrouped) — fields that identify the entity: `name`, `description`, `status`, `domain`, etc.
3. **Relationships** — foreign key IDs grouped together: `profile_id`, `company_id`, `property_id`, etc.
4. **Strings** — remaining string fields
5. **Integers** — non-FK integer fields
6. **Numerics** — decimal/float fields: `cost`, `price`, `total`, etc.
7. **Booleans** — boolean fields
8. **Dates** — date-only fields
9. **Timestamps** — entity-specific first, then standard `created_at`, `updated_at`, `deleted_at` last
10. **Nested objects** — JSON objects/arrays without casting
11. **Loader metadata** — system columns from your ingestion tool (see below)

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
-- loader metadata
```

### Standard Timestamp Fields

Always include these at the end of the timestamps section (before nested objects), if they exist in the source data:
```sql
cast(created_at as {{ type_timestamp() }}) as created_at,
cast(updated_at as {{ type_timestamp() }}) as updated_at,
cast(deleted_at as {{ type_timestamp() }}) as deleted_at,
```

### Nested Objects

Leave nested objects (arrays or objects) without casting. Place at the end before loader metadata:
```sql
custom as custom,
custom_with_labels as custom_with_labels,
options as options,
```

For guidance on when to unnest objects inline vs. create separate flattened models, see [dbt-staging](../dbt-staging/SKILL.md) Step 6.

### Loader Metadata Block

Always include loader-specific metadata columns at the end of the select, after nested objects. The exact columns depend on your ingestion tool. See the [Loader-Specific Considerations](../dbt-staging/SKILL.md#loader-specific-considerations) section in the dbt-staging skill for details on each loader's metadata pattern.

### Quick Example

Given this source data:
```
| account_id | name            | close_rate | is_active | options              | created_at                    |
|------------|-----------------|------------|-----------|----------------------|-------------------------------|
| 555078     | Example Company | 0.0500     | true      | { "setting": true }  | 2025-08-22T00:24:14+00:00     |
```

Transform to:
```sql
-- identifiable info (ungrouped)
cast(name as {{ type_string() }}) as company_name,

-- relationships
cast(account_id as {{ type_int() }}) as account_id,

-- numerics
cast(close_rate as {{ type_numeric() }}) as close_rate,

-- booleans
cast(is_active as {{ type_boolean() }}) as is_active,

-- timestamps
cast(created_at as {{ type_timestamp() }}) as created_at,

-- nested objects
options as options,
```

### Full Example

See [examples/stg_source__entities.sql](examples/stg_source__entities.sql) for a complete staging model with all column groups.

## Related Skills

- **[dbt-style](../dbt-style/SKILL.md)** — Foundational naming, SQL style, and structure conventions
- **[dbt-staging](../dbt-staging/SKILL.md)** — Full staging workflow including complex structure handling and loader-specific metadata
- **[dbt-mcp](../dbt-mcp/SKILL.md)** — Use `compile` to verify Jinja rendering, `show` to preview results

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

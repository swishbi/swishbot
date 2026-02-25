# Transform Staging Models

Inspect source data and transform each staging model with proper casting, renaming, and complex structure handling.

## Step 1: Inspect Source Data

Before transforming staging models, inspect data from each source table to understand column structure, data types, and nested fields. Use the dbt MCP **`show`** tool to preview source data:

```sql
select * from {{ source('<source_name>', '<table_name>') }} limit 10
```

Use the results to:

- Identify column types and determine the correct cast for each
- Spot camelCase field names that need snake_case conversion
- Identify JSON/variant columns that contain nested data
- Find nullable fields and fields with unexpected formats
- Identify tables with no data (empty tables)

**Handling empty tables:** Some source tables may not yet have data loaded. These should be:
1. Marked with `config: enabled: false` in the source YAML (under the table entry)
2. Given a disabled stub staging model:

```sql
{{ config(enabled=false) }}

with source as (
    select * from {{ source('<source_name>', '<table_name>') }}
),
renamed as (
    select
        *
    from source
)
select * from renamed
```

## Step 2: Transform Each Staging Model

After inspecting the source data, update each active staging SQL file to follow the **staging SQL conventions**. Use the sample data from Step 1 to make informed decisions about column casting and naming. This includes:

- SQL CTE structure (`source` -> `renamed` -> `select *`)
- Column casting with dbt type macros
- camelCase to snake_case renaming
- Grouped column ordering (primary key, identifiable info, relationships, strings, integers, numerics, booleans, dates, timestamps, nested objects, loader metadata)

See [references/staging-sql-conventions.md](../../references/staging-sql-conventions.md) for the full reference on casting rules, naming conventions, column ordering, and SQL structure.

## Step 3: Handle Complex Data Structures

When inspecting source data, classify nested/complex columns into two categories:

### Same-grain objects (unnest inline)

The nested column contains a single JSON object whose fields describe the same row. These should be **unnested** — extract each scalar field from the object and cast it with the appropriate dbt type macro. Remove the original nested column after extracting its fields.

Use the dbt MCP `show` tool to inspect the nested column values:
```sql
select <nested_column> from {{ source('<source_name>', '<table_name>') }} limit 10
```

If the value starts with `{`, it's a single object (same grain). Convert field names from camelCase to snake_case and group unnested fields logically.

**Unnesting syntax by warehouse:**

| Warehouse | Syntax | Example |
|-----------|--------|---------|
| **Snowflake** | `column:FieldName` | `cast(vendor_ref:value as {{ type_string() }}) as vendor_id` |
| **BigQuery** | `column.FieldName` | `cast(vendor_ref.value as {{ type_string() }}) as vendor_id` |
| **Databricks** | `column.FieldName` or `column:FieldName` | `cast(vendor_ref.value as {{ type_string() }}) as vendor_id` |
| **Redshift** | `json_extract_path_text(column, 'FieldName')` | `cast(json_extract_path_text(vendor_ref, 'value') as varchar) as vendor_id` |

**Example — reference objects** with `{value, name}` structure:
```sql
-- relationships
cast(vendor_ref:value as {{ type_string() }}) as vendor_id,
cast(vendor_ref:name as {{ type_string() }}) as vendor_name,
```

**Example — address objects:**
```sql
-- billing address
cast(bill_addr:Id as {{ type_string() }}) as bill_address_id,
cast(bill_addr:Line1 as {{ type_string() }}) as bill_address_line1,
cast(bill_addr:City as {{ type_string() }}) as bill_address_city,
cast(bill_addr:CountrySubDivisionCode as {{ type_string() }}) as bill_address_state,
cast(bill_addr:PostalCode as {{ type_string() }}) as bill_address_postal_code,
```

### Different-grain arrays (create separate flattened models)

If the value starts with `[`, it's an array of objects at a different grain than the parent row (e.g., line items on an invoice). These should remain as nested columns in the parent staging model and get their own flattened staging model.

**Naming convention:** `stg_<source_name>__<parent_table>__<array_column>`

For example, if `stg_quickbooks__bill` has a `line` array column, create `stg_quickbooks__bill__line`.

**Flattened model structure:**

Each flattened model should:
- Select from the raw `source()` (not the parent staging model)
- Include the parent's primary key as a foreign key
- Flatten the array using warehouse-specific syntax (see below)
- Extract level-1 scalar fields from each array element, cast with dbt type macros
- **Apply same-grain unnesting** to nested objects within array elements
- Keep any nested **arrays** within array elements as variant/JSON columns
- Include loader metadata columns from the parent row

**Warehouse-specific flatten syntax:**

| Warehouse | Syntax | Field Access |
|-----------|--------|--------------|
| **Snowflake** | `lateral flatten(input => source.array_col) as item` | `item.value:FieldName` |
| **BigQuery** | `cross join unnest(array_col) as item` | `item.FieldName` |
| **Databricks** | `lateral view explode(array_col) as item` | `item.FieldName` |
| **Redshift** | `cross join ... (JSON extract pattern)` | Varies |

**Example (Snowflake):**

```sql
with source as (
    select * from {{ source('<source_name>', '<table_name>') }}
),
flattened as (
    select
        -- parent key
        source.id as <parent>_id,

        -- array element fields
        cast(item.value:Id as {{ type_string() }}) as line_id,
        cast(item.value:Amount as {{ type_numeric() }}) as amount,
        cast(item.value:Description as {{ type_string() }}) as description,

        -- same-grain nested object within element (unnested)
        cast(item.value:DetailObject:AccountRef:value as {{ type_string() }}) as account_id,
        cast(item.value:DetailObject:AccountRef:name as {{ type_string() }}) as account_name,

        -- nested arrays within element (stay as variant)
        item.value:LinkedTxn as linked_txn,

        -- loader metadata
        source._dlt_id,
        source._dlt_load_id

    from source,
    lateral flatten(input => source.<array_column>) as item
)
select * from flattened
```

Create a `.yml` file for each flattened model as well.

## Checklist

- [ ] Source data inspected with dbt MCP `show` tool for each table
- [ ] Empty tables identified and disabled (`config: enabled: false` + stub SQL)
- [ ] Each active staging model transformed to follow staging SQL conventions (see references/staging-sql-conventions.md)
- [ ] Complex structures handled (same-grain unnested, arrays get flattened models)
- [ ] Flattened models created for array columns (`stg_<source>__<parent>__<array>`)
- [ ] Column casting, renaming, and ordering applied

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

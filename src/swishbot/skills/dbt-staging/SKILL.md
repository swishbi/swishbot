---
name: dbt-staging
description: "Build the staging/bronze layer in dbt. Use when a source system needs to be staged with consistent naming, typing, and light transformations. Applies regardless of warehouse platform or ingestion tool."
---

# dbt Staging Layer

## Overview

The staging layer is the first transformation layer in dbt. It sits directly on top of raw source data and provides a clean, consistently shaped interface for downstream models. This skill walks through the full workflow: discovering sources, generating YAML, creating staging models, inspecting data, handling complex structures, and validating.

This skill is **loader-agnostic** — the core workflow applies whether data is loaded by dlt, Fivetran, Airbyte, Stitch, custom scripts, or any other ingestion tool. Loader-specific considerations (metadata columns, SCD patterns) are covered in a dedicated section.

Official reference: https://docs.getdbt.com/best-practices/how-we-structure/2-staging

## Prerequisites

- Source data must already be loaded into your warehouse (via any ingestion method)
- The `codegen` dbt package must be installed (`dbt deps`)
- The dbt MCP server should be configured (see [dbt-mcp](../dbt-mcp/SKILL.md))
- You must know the schema name that contains the source tables

## Instructions

### Step 1: Generate the Source YAML

Run the `generate_source` macro (or use the dbt MCP `generate_source` tool if codegen is enabled) to produce the source definition file. Include the `table_names` argument to specify exactly which tables to generate.

#### Finding table names

Use the dbt MCP `show` tool to query the information schema for tables in the source schema:

```sql
select table_name
from information_schema.tables
where table_schema = '<source_schema>'
order by table_name
```

Alternatively, check the ingestion tool's documentation or UI for the list of synced tables.

**Loader-specific tables:** Some loaders create internal metadata tables (e.g., dlt creates `_dlt_loads`, `_dlt_pipeline_state`, `_dlt_version`; Fivetran creates `fivetran_audit`). Include these in your source YAML for completeness but you typically won't create staging models for them.

#### Running the macro

```bash
cd transformation && dbt --quiet run-operation generate_source \
  --args '{"schema_name": "<source_name>", "database_name": "<database_name>", "generate_columns": true, "include_descriptions": true, "include_data_types": false, "table_names": ["<table_1>", "<table_2>", "<table_n>"]}' \
  > models/staging/<source_name>/_<source_name>__sources.yml
```

Create the staging directory first if it doesn't exist:
```bash
mkdir -p transformation/models/staging/<source_name>
```

After generating, update the source YAML header to include dynamic database/schema references:

```yaml
version: 2

sources:
  - name: <source_name>
    description: ""
    database: "{{ var('<source_name>_database', '<default_database>') }}"
    schema: "{{ var('<source_name>_schema', '<source_name>') }}"

    tables:
      ...
```

### Step 2: Add Data Tests to the Source YAML

For each table in the source YAML (excluding loader-internal metadata tables), add data tests for the primary key.

#### Standard test pattern

Every source table needs at minimum:

1. A **column-level** `not_null` test on the primary key column
2. A **column-level** `unique` test on the primary key column

```yaml
      - name: <table_name>
        description: ""
        columns:
          - name: id
            description: ""
            data_tests:
              - not_null
              - unique
```

For sources with SCD2 / versioned rows, see the [Loader-Specific Considerations](#loader-specific-considerations) section for adapted test patterns.

### Step 3: Generate Base Staging Models

Run the `create_base_models` macro to generate bash commands for creating staging SQL files:

```bash
cd transformation && dbt run-operation codegen.create_base_models \
  --args '{source_name: <source_name>, tables: ["table_1", "table_2", "table_n"]}'
```

This outputs shell commands that create individual `stg_<source_name>__<table_name>.sql` files in `models/staging/<source_name>/`. Run the output commands from the `transformation/` directory.

### Step 4: Inspect Source Data

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

### Step 5: Transform Each Staging Model

After inspecting the source data, update each active staging SQL file to follow the **dbt-staging-model** skill conventions. Use the sample data from Step 4 to make informed decisions about column casting and naming. This includes:

- SQL CTE structure (`source` -> `renamed` -> `select *`)
- Column casting with dbt type macros
- camelCase to snake_case renaming
- Grouped column ordering (primary key, identifiable info, relationships, strings, integers, numerics, booleans, dates, timestamps, nested objects, loader metadata)

See the [dbt-staging-model](../dbt-staging-model/SKILL.md) skill for the full reference on casting rules, naming conventions, column ordering, and SQL structure.

### Step 6: Handle Complex Data Structures

When inspecting source data, classify nested/complex columns into two categories:

#### Same-grain objects (unnest inline)

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

#### Different-grain arrays (create separate flattened models)

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

### Step 7: Create Model YAML Files

Create a YAML file for each staging model (both parent and flattened, both active and disabled):

```yaml
version: 2

models:
  - name: stg_<source_name>__<table_name>
    description: ""
```

Create one `.yml` file per `.sql` file, with matching names.

### Step 8: Validate

Build the staging models to verify everything works:

```bash
cd transformation && dbt build --select staging.<source_name>
```

Use the dbt MCP `show` tool to preview results of individual models:

```sql
select * from {{ ref('stg_<source_name>__<table_name>') }} limit 10
```

## Checklist

- [ ] Source YAML generated with `generate_source` macro
- [ ] Database/schema references updated to use Jinja vars
- [ ] Data tests added for all non-metadata tables
- [ ] Base staging models created via `create_base_models`
- [ ] Source data inspected with dbt MCP `show` tool for each table
- [ ] Empty tables identified and disabled (`config: enabled: false` + stub SQL)
- [ ] Each active staging model transformed to follow dbt-staging-model conventions
- [ ] Complex structures handled (same-grain unnested, arrays get flattened models)
- [ ] Flattened models created for array columns (`stg_<source>__<parent>__<array>`)
- [ ] Model YAML file created for each staging model (`.yml` per `.sql`)
- [ ] Column casting, renaming, and ordering applied
- [ ] Loader metadata columns included
- [ ] `dbt build` passes for the new source

## Loader-Specific Considerations

### dlt

dlt adds metadata columns to every table: `_dlt_id`, `_dlt_load_id`. When SCD2 is enabled, it also adds `_dlt_valid_from` and `_dlt_valid_to`.

**Internal metadata tables** (include in source YAML but do not stage):
- `_dlt_loads`, `_dlt_pipeline_state`, `_dlt_version`

**Finding table names from dlt:**

```bash
dlt pipeline <source_name>_pipeline sync && dlt pipeline <source_name>_pipeline schema
```

Or inspect the `"resources"` block in the pipeline source code.

**dlt metadata block in staging models:**

```sql
-- dlt metadata
_dlt_id,
_dlt_load_id,
{%- if var('<source_name>_scd2_enabled', false) or ('scd2' in (env_var('SOURCES__<SOURCE_NAME_UPPER>_PIPELINE__WRITE_DISPOSITION', '') | lower)) %}
_dlt_valid_from,
_dlt_valid_to,
row_number() over (partition by id order by _dlt_valid_from) as _dlt_version,
{%- endif %}
'<source_name>' as _dlt_source
```

The SCD2 block and `where` clause use a dual check pattern — SCD2 can be enabled via either a dbt var or an environment variable:

```sql
{%- if var('<source_name>_scd2_enabled', false) or ('scd2' in (env_var('SOURCES__<SOURCE_NAME_UPPER>_PIPELINE__WRITE_DISPOSITION', '') | lower)) %}
where _dlt_valid_to is null
{%- endif %}
```

Add the SCD2 variable to `dbt_project.yml`:

```yaml
vars:
  <source_name>_scd2_enabled: true  # or false
```

**SCD2-aware data tests:**

```yaml
      - name: <table_name>
        description: ""
        data_tests:
          - dbt_utils.unique_combination_of_columns:
              combination_of_columns:
                - _dlt_id
                - _dlt_valid_from
              config:
                enabled: "{{ var('<source_name>_scd2_enabled', false) or ('scd2' in (env_var('SOURCES__<SOURCE_NAME_UPPER>_PIPELINE__WRITE_DISPOSITION', '') | lower)) }}"
                severity: warn
        columns:
          - name: id
            description: ""
            data_tests:
              - not_null
              - unique:
                  config:
                    enabled: "{{ not var('<source_name>_scd2_enabled', false) and ('scd2' not in (env_var('SOURCES__<SOURCE_NAME_UPPER>_PIPELINE__WRITE_DISPOSITION', '') | lower)) }}"
                    severity: warn
          - name: _dlt_id
            description: ""
            data_tests:
              - not_null
              - unique:
                  config:
                    enabled: "{{ not var('<source_name>_scd2_enabled', false) and ('scd2' not in (env_var('SOURCES__<SOURCE_NAME_UPPER>_PIPELINE__WRITE_DISPOSITION', '') | lower)) }}"
                    severity: warn
```

### Fivetran

Fivetran adds metadata columns: `_fivetran_synced` (timestamp of last sync) and `_fivetran_deleted` (soft-delete boolean, if enabled).

**Internal metadata tables** (include in source YAML but do not stage):
- `fivetran_audit`

**Fivetran metadata block in staging models:**

```sql
-- fivetran metadata
_fivetran_synced,
_fivetran_deleted
```

**Soft-delete filtering:** If the connector has soft-delete enabled, filter out deleted rows:

```sql
from source
where not coalesce(_fivetran_deleted, false)
```

### Airbyte

Airbyte adds metadata columns: `_airbyte_raw_id`, `_airbyte_extracted_at`, `_airbyte_meta`. With deduped sync mode, it may also add `_airbyte_generation_id`.

**Airbyte metadata block in staging models:**

```sql
-- airbyte metadata
_airbyte_raw_id,
_airbyte_extracted_at,
_airbyte_meta
```

### Other Loaders

For loaders not listed above, inspect the raw tables to identify any system-generated metadata columns. Include them in a `-- <loader> metadata` section at the end of the select, following the same pattern.

## Examples

See [examples/](examples/) for reference files:
- `_source__sources.yml` — Source YAML with primary key tests
- `stg_source__entities.sql` — Staging model with full conventions

## Related Skills

- **[dbt-style](../dbt-style/SKILL.md)** — Foundational naming, SQL style, and structure conventions
- **[dbt-staging-model](../dbt-staging-model/SKILL.md)** — Detailed SQL conventions for staging model files
- **[dbt-intermediate](../dbt-intermediate/SKILL.md)** — The downstream layer consuming staging models
- **[dbt-mcp](../dbt-mcp/SKILL.md)** — Use `show` to inspect source data and preview model results
- **[dlt-pipelines](../dlt-pipelines/SKILL.md)** — Build dlt ingestion pipelines that feed into staging models
- **[dba-security](../dba-security/SKILL.md)** — Database separation strategy that determines where raw and staging data live

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

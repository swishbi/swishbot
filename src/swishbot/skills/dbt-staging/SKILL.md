---
name: dbt-staging
description: "Build the staging/bronze layer in dbt. Use when a source system needs to be staged with consistent naming, typing, and light transformations. Applies regardless of warehouse platform (Snowflake, BigQuery, Databricks, etc.)."
---

# dbt Staging Layer

## Overview

The staging layer is the first transformation layer in dbt. It sits directly on top of raw source data and provides a clean, consistently shaped interface for downstream models. Stage a new source system in dbt using the codegen package. This skill walks through generating source YAML, creating base staging models, and transforming them to follow project conventions.

Official reference: https://docs.getdbt.com/best-practices/how-we-structure/2-staging

## Prerequisites

- The source data must already be loaded into Snowflake (via a dlt pipeline or other ingestion method)
- The `codegen` dbt package must be installed (`dbt deps`)
- You must know the schema name in Snowflake that contains the source tables

## Usage

Provide the source name (schema name in Snowflake) and Claude will walk through each step.

## Instructions

### Step 1: Generate the Source YAML

Run the `generate_source` macro to produce the source definition file. You must include the `table_names` argument to specify exactly which tables to generate — this includes all resource tables from the dlt pipeline plus the `_dlt_loads`, `_dlt_pipeline_state`, and `_dlt_version` metadata tables.

#### Finding table names

**Option A — From the dlt pipeline schema (most reliable):**

Sync and inspect the pipeline schema to get the authoritative list of tables:

```bash
dlt pipeline <source_name>_pipeline sync && dlt pipeline <source_name>_pipeline schema
```

Look at the table keys in the schema output. These are the exact table names in Snowflake.

**Option B — From the pipeline source code:**

Look at the `"resources"` block of the `RESTAPIConfig` in `ingestion/<source_name>/<source_name>_pipeline.py`. Resource names listed there correspond to the table names in Snowflake. For example:

```python
"resources": [
    "companies",
    "employees",
    "work_orders",
]
```

In both cases, combine the resource/schema tables with the dlt metadata tables to get the full `table_names` list — e.g. `["companies", "employees", "work_orders", "_dlt_loads", "_dlt_pipeline_state", "_dlt_version"]`.

#### Running the macro

Pipe the output directly to the correct file path.

```bash
cd transformation && dbt --quiet run-operation generate_source --args '{"schema_name": "<source_name>", "database_name": "<database_name>", "generate_columns": true, "include_descriptions": true, "include_data_types": false, "table_names": ["<table_1>", "<table_2>", "<table_n>", "_dlt_loads", "_dlt_pipeline_state", "_dlt_version"]}' > models/staging/<source_name>/_<source_name>__sources.yml
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
    database: "{{ var('<source_name>_database', 'raw' if target.name == 'prod' else 'raw_dev') }}"
    schema: "{{ var('<source_name>_schema', '<source_name>') }}"

    tables:
      ...
```

### Step 2: Add Data Tests to the Source YAML

For each table in the source YAML (excluding `_dlt_loads`, `_dlt_pipeline_state`, `_dlt_version` metadata tables), add data tests that gracefully handle SCD2 scenarios.

#### Test Pattern for SCD2-enabled sources

Each table needs:

1. A **table-level** `unique_combination_of_columns` test on `_dlt_id` + `_dlt_valid_from`, enabled only when SCD2 is active
2. A **column-level** `not_null` test on the `id` column
3. A **column-level** `unique` test on the `id` or primary key column, enabled only when SCD2 is NOT active
4. A **column-level** `not_null` test on `_dlt_id`
5. A **column-level** `unique` test on `_dlt_id`, enabled only when SCD2 is NOT active

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
          - name: type
            description: ""
          - name: id
            description: ""
            data_tests:
              - not_null
              - unique:
                  config:
                    enabled: "{{ not var('<source_name>_scd2_enabled', false) and ('scd2' not in (env_var('SOURCES__<SOURCE_NAME_UPPER>_PIPELINE__WRITE_DISPOSITION', '') | lower)) }}"
                    severity: warn
          - name: attributes
            description: ""
          - name: _dlt_id
            description: ""
            data_tests:
              - not_null
              - unique:
                  config:
                    enabled: "{{ not var('<source_name>_scd2_enabled', false) and ('scd2' not in (env_var('SOURCES__<SOURCE_NAME_UPPER>_PIPELINE__WRITE_DISPOSITION', '') | lower)) }}"
                    severity: warn
          - name: _dlt_load_id
            description: ""
          - name: _dlt_valid_from
            description: ""
          - name: _dlt_valid_to
            description: ""
```

Replace `<SOURCE_NAME_UPPER>` with the uppercase version of the source name (e.g., `source` -> `SOURCE`).

**Important:** The `_dlt_loads`, `_dlt_pipeline_state`, and `_dlt_version` tables are dlt internal metadata tables. Do NOT add SCD2 tests to these. Leave them as-is from the codegen output.

### Step 3: Generate the Base Model Creation Commands

Run the `create_base_models` macro to generate bash commands for creating staging SQL files. You need to pass all table names from the source YAML (excluding `_dlt_*` metadata tables).

```bash
cd transformation && dbt run-operation codegen.create_base_models --args '{source_name: <source_name>, tables: ["table_1", "table_2", "table_n"]}'
```

This outputs a series of bash commands that reference the package path (`dbt_packages/codegen/bash_scripts/base_model_creation.sh`). You must replace that path with `analyses/code_generators/base_model_creation.sh` before running, so the commands look like:

```bash
source analyses/code_generators/base_model_creation.sh <source_name> table_1 &&
source analyses/code_generators/base_model_creation.sh <source_name> table_2 &&
source analyses/code_generators/base_model_creation.sh <source_name> table_n
```

Also append the commands to `analyses/code_generators/create_stg_models.sh` for reproducibility:

```bash
dbt run-operation codegen.create_base_models --args '{source_name: <source_name>, tables: ["table_1", "table_2", "table_n"]}'
```

### Step 4: Run the Base Model Creation Commands

Execute the output commands from Step 3. These must be run from the `transformation/` directory. They create individual `stg_<source_name>__<table_name>.sql` files in `models/staging/<source_name>/`.

```bash
cd transformation && \
source analyses/code_generators/base_model_creation.sh <source_name> table_1 && \
source analyses/code_generators/base_model_creation.sh <source_name> table_2 && \
source analyses/code_generators/base_model_creation.sh <source_name> table_n
```

Also append the commands to `analyses/code_generators/generate_stg_models.sh` for reproducibility:

```bash
# <source_name> stg models
source analyses/code_generators/base_model_creation.sh <source_name> table_1 &&
source analyses/code_generators/base_model_creation.sh <source_name> table_2 &&
source analyses/code_generators/base_model_creation.sh <source_name> table_n
```

### Step 5: Inspect Source Data and Identify Empty Tables

Before transforming staging models, sample data from each source table to understand the column structure, JSON field names, and data types. Use the `get_source_sample` macro which calls `dbt_utils.get_query_results_as_dict` under the hood.

**Identifying empty tables:** Some source tables may not yet exist in Snowflake (the pipeline defines them but no data has been loaded). These tables should be:
1. Marked with `config: enabled: false` in the source YAML (under the table entry)
2. Given a disabled stub staging model with `{{ config(enabled=false) }}` and a simple `select *` placeholder
3. Excluded from Steps 3-4 (base model generation) since there's no data to inspect

Run this for **each** non-metadata table (exclude `_dlt_loads`, `_dlt_pipeline_state`, `_dlt_version`):

```bash
cd transformation && dbt --quiet run-operation get_source_sample --args '{"source_name": "<source_name>", "table_name": "<table_name>"}'
```

This returns a dictionary where keys are column names (uppercase) and values are lists of sample data (up to 500 rows). Use the results to:

- Identify the JSON column (e.g., `ATTRIBUTES`) and its nested field names
- Determine the correct data type for each field (string, integer, numeric, timestamp, boolean, nested object)
- Spot camelCase field names that need snake_case conversion
- Identify nested objects/arrays that should remain uncast
- Find nullable fields and fields with unexpected formats

**Handling nested objects:** When inspecting nested columns, determine whether each is at the **same grain** (a single object per row) or a **different grain** (an array of objects).

- **Same grain** — the nested column contains a single JSON object whose fields describe the same row. These should be **unnested** using Snowflake variant syntax (`column:FieldName`) and cast to appropriate types. Remove the original nested column after extracting its fields.
- **Different grain** — the nested column contains an **array** of objects (i.e., line-level detail, a list of related records, etc.). These should remain as nested variant columns for downstream unnesting in intermediate/marts models.

Use `get_source_sample` to inspect actual values and determine which category each column falls into. If the value starts with `[` it's an array; if it starts with `{` it's an object.

**Unnesting conventions:**
- Extract each scalar field from the object and cast it with the appropriate dbt type macro
- Convert field names from camelCase to snake_case
- Group unnested fields logically (e.g., all address fields together under an `-- <prefix> address` comment, all ref fields under `-- relationships`)

**Example — QuickBooks `_ref` objects** are same-grain objects with `{value, name}` structure:
```sql
-- relationships
cast(vendor_ref:value as {{ type_string() }}) as vendor_id,
cast(vendor_ref:name as {{ type_string() }}) as vendor_name,
```

**Example — QuickBooks address objects** are same-grain with `{Id, Line1, Line2, City, CountrySubDivisionCode, PostalCode, Country}`:
```sql
-- billing address
cast(bill_addr:Id as {{ type_string() }}) as bill_address_id,
cast(bill_addr:Line1 as {{ type_string() }}) as bill_address_line1,
cast(bill_addr:City as {{ type_string() }}) as bill_address_city,
cast(bill_addr:CountrySubDivisionCode as {{ type_string() }}) as bill_address_state,
cast(bill_addr:PostalCode as {{ type_string() }}) as bill_address_postal_code,
```

**Example — arrays that stay nested:** `line` (transaction line items), `linked_txn` (related transactions), `custom_field`, `budget_detail`.

### Step 6: Create Disabled Stubs for Empty Tables

For any tables identified as empty/missing in Step 5, create a disabled stub staging model. This reserves the file and follows the naming convention so it's ready to be fleshed out when data arrives.

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

Also set `config: enabled: false` on the table entry in the source YAML so the source tests are skipped:

```yaml
      - name: <table_name>
        description: ""
        config:
          enabled: false
        data_tests:
          ...
```

### Step 7: Transform Each Staging Model

After inspecting the source data, update each active staging SQL file to follow the **dbt-staging-model** skill conventions. Use the sample data from Step 5 to make informed decisions about column casting and naming. This includes:

- SQL CTE structure (`source` -> `renamed` -> `select *`)
- Column casting with dbt type macros
- camelCase to snake_case renaming
- Grouped column ordering (primary key, identifiable info, relationships, strings, integers, numerics, booleans, dates, timestamps, nested objects, dlt metadata)
- SCD2-aware dlt metadata block with dual check pattern

See the [dbt-staging-model](../dbt-staging-model/SKILL.md) skill for the full reference on casting rules, naming conventions, column ordering, and SQL structure.

### Step 8: Create Flattened Models for Array Columns

After transforming the parent staging models, identify any remaining **nested array columns** (columns that contain a JSON array of objects at a different grain than the parent row). For each array column, create a separate flattened staging model that explodes the array into one row per element.

**Naming convention:** `stg_<source_name>__<parent_table>__<array_column>`

For example, if `stg_quickbooks__bill` has a `line` array column, create `stg_quickbooks__bill__line`.

**Flattened model structure:**

Each flattened model should:
- Select from the raw `source()` (not the parent staging model)
- Include the parent's primary key as a foreign key
- Flatten the array using the warehouse-specific syntax (see below)
- Extract level-1 scalar fields from each array element, cast with dbt type macros
- **Apply same-grain unnesting** to nested objects within array elements — if an element field contains a single JSON object (not an array), unnest its scalar fields inline with casts. This is the deepest level of unnesting for this skill.
- Keep any nested **arrays** within the array elements as variant columns
- Include `_dlt_id`, `_dlt_load_id`, and SCD2 columns from the parent
- Include `_dlt_source` literal
- Apply the SCD2 `where _dlt_valid_to is null` filter

**Warehouse-specific flatten syntax:**

| Warehouse | Syntax | Field Access |
|-----------|--------|--------------|
| **Snowflake** | `from source, lateral flatten(input => source.array_col) as alias` | `alias.value:FieldName` |
| **BigQuery** | `cross join unnest(array_col) as alias` | `alias.FieldName` |
| **Databricks** | `lateral view explode(array_col) as alias` | `alias.FieldName` |
| **Redshift** | `cross join ... (unpivot/JSON extract pattern)` | Varies |

**Snowflake example:**

```sql
with source as (
    select * from {{ source('<source_name>', '<table_name>') }}
    {%- if var('<source_name>_scd2_enabled', false) or (...) %}
    where _dlt_valid_to is null
    {%- endif %}
),
flattened as (
    select
        -- parent key
        source.id as <parent>_id,
        -- array element fields
        cast(item.value:Id as {{ type_string() }}) as line_id,
        cast(item.value:Amount as {{ type_numeric() }}) as amount,
        cast(item.value:Description as {{ type_string() }}) as description,
        -- same-grain nested object (unnested)
        cast(item.value:SomeDetailObject:AccountRef:value as {{ type_string() }}) as account_id,
        cast(item.value:SomeDetailObject:AccountRef:name as {{ type_string() }}) as account_name,
        cast(item.value:SomeDetailObject:Status as {{ type_string() }}) as status,
        -- nested arrays within the array element (stay as variant)
        item.value:LinkedTxn as linked_txn,
        -- dlt metadata
        source._dlt_id,
        source._dlt_load_id,
        {%- if var('<source_name>_scd2_enabled', false) or (...) %}
        source._dlt_valid_from,
        source._dlt_valid_to,
        {%- endif %}
        '<source_name>' as _dlt_source
    from source,
    lateral flatten(input => source.<array_column>) as item
)
select * from flattened
```

Create a `.yml` file for each flattened model as well.

### Step 9: Create Model YAML Files

Create a YAML file for each staging model (both parent and flattened, both active and disabled). Each file follows the same simple pattern:

```yaml
version: 2

models:
  - name: stg_<source_name>__<table_name>
    description: ""
```

Create one `.yml` file per `.sql` file, with matching names (e.g., `stg_quickbooks__account.sql` gets `stg_quickbooks__account.yml`). These files are stubs for adding column descriptions and model-level tests later.

### Step 10: Add dbt_project.yml Variable

Add the SCD2 variable for the new source to `dbt_project.yml` under the `vars` section:

```yaml
vars:
  <source_name>_scd2_enabled: true  # or false, depending on whether SCD2 is active
```

### Step 11: Validate

Build the staging models to verify everything works:

```bash
cd transformation && dbt build --select staging.<source_name>
```

## Checklist

- [ ] Source YAML generated with `generate_source` macro
- [ ] Database/schema references updated to use Jinja vars
- [ ] Data tests added for all non-metadata tables (SCD2-aware)
- [ ] Base models created via `create_base_models` / `base_model_creation.sh`
- [ ] Commands appended to `generate_stg_models.sh`
- [ ] Source data inspected with `get_source_sample` for each table
- [ ] Empty tables identified and disabled (`config: enabled: false` in source YAML + stub SQL)
- [ ] Each active staging model transformed to follow project conventions
- [ ] Flattened models created for array columns (`stg_<source>__<parent>__<array>`)
- [ ] Model YAML file created for each staging model (`.yml` per `.sql`)
- [ ] Column casting, renaming, and ordering applied
- [ ] SCD2 handling added to each model (dlt metadata block)
- [ ] `_dlt_source` literal set to source name
- [ ] SCD2 variable added to `dbt_project.yml`
- [ ] `dbt build` passes for the new source

## Examples

See [examples/](examples/) for reference files:
- `_source__sources.yml` - Source YAML with SCD2 tests
- `stg_source__entities.sql` - Staging model with full conventions

## Related Skills

- **[dbt-style](../dbt-style/SKILL.md)** — Foundational naming, SQL style, and structure conventions
- **[dbt-staging-model](../dbt-staging-model/SKILL.md)** — Detailed SQL conventions for staging model files
- **[dbt-intermediate](../dbt-intermediate/SKILL.md)** — The downstream layer consuming staging models
- **[dbt-mcp](../dbt-mcp/SKILL.md)** — Use `generate_source` and `generate_staging_model` MCP tools to scaffold boilerplate

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

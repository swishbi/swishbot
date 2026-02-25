# Create Staging Source

Set up the source definition and base staging models for a new source system.

## Step 1: Generate the Source YAML

Run the `generate_source` macro (or use the dbt MCP `generate_source` tool if codegen is enabled) to produce the source definition file. Include the `table_names` argument to specify exactly which tables to generate.

### Finding table names

Use the dbt MCP `show` tool to query the information schema for tables in the source schema:

```sql
select table_name
from information_schema.tables
where table_schema = '<source_schema>'
order by table_name
```

Alternatively, check the ingestion tool's documentation or UI for the list of synced tables.

**Loader-specific tables:** Some loaders create internal metadata tables (e.g., dlt creates `_dlt_loads`, `_dlt_pipeline_state`, `_dlt_version`; Fivetran creates `fivetran_audit`). Include these in your source YAML for completeness but you typically won't create staging models for them.

### Running the macro

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

## Step 2: Add Data Tests to the Source YAML

For each table in the source YAML (excluding loader-internal metadata tables), add data tests for the primary key.

### Standard test pattern

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

For sources with SCD2 / versioned rows, see [loader-metadata.md](../../references/loader-metadata.md) for adapted test patterns.

## Step 3: Generate Base Staging Models

Run the `create_base_models` macro to generate bash commands for creating staging SQL files:

```bash
cd transformation && dbt run-operation codegen.create_base_models \
  --args '{source_name: <source_name>, tables: ["table_1", "table_2", "table_n"]}'
```

This outputs shell commands that create individual `stg_<source_name>__<table_name>.sql` files in `models/staging/<source_name>/`. Run the output commands from the `transformation/` directory.

## Checklist

- [ ] Source YAML generated with `generate_source` macro
- [ ] Database/schema references updated to use Jinja vars
- [ ] Data tests added for all non-metadata tables
- [ ] Base staging models created via `create_base_models`

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

# Loader-Specific Metadata

This reference covers the metadata columns and patterns added by common ingestion tools. Apply the relevant section when building staging models for a source loaded by one of these tools.

## dlt

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

## Fivetran

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

## Airbyte

Airbyte adds metadata columns: `_airbyte_raw_id`, `_airbyte_extracted_at`, `_airbyte_meta`. With deduped sync mode, it may also add `_airbyte_generation_id`.

**Airbyte metadata block in staging models:**

```sql
-- airbyte metadata
_airbyte_raw_id,
_airbyte_extracted_at,
_airbyte_meta
```

## Other Loaders

For loaders not listed above, inspect the raw tables to identify any system-generated metadata columns. Include them in a `-- <loader> metadata` section at the end of the select, following the same pattern.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

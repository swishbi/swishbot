/*
generate_schema_name (environment-aware override)
==================================================
Controls which schema dbt writes each model to.

dbt's default concatenates target.schema with custom_schema_name in ALL
environments (e.g., dbt_jsmith_staging everywhere). This is not what we
want — in production, models should write to bare schema names.

This override delegates to dbt's built-in generate_schema_name_for_env
which applies the following logic:

  - Production (target.name = 'prod'):
      custom_schema_name provided  → uses custom_schema_name directly
      no custom_schema_name        → uses target.schema

  - Development / CI:
      custom_schema_name provided  → target.schema ~ '_' ~ custom_schema_name
      no custom_schema_name        → uses target.schema

Examples (target.schema = 'dbt_jsmith', target.name = 'dev'):
  +schema: staging       → dbt_jsmith_staging
  +schema: marts         → dbt_jsmith_marts
  (no custom schema)     → dbt_jsmith

Examples (target.schema = 'dbt_cloud', target.name = 'prod'):
  +schema: staging       → staging
  +schema: marts         → marts
  (no custom schema)     → dbt_cloud

IMPORTANT: Never remove the target.schema fallback — without it,
developers would write directly to shared schemas and overwrite
each other's work.

Reference: https://docs.getdbt.com/docs/build/custom-schemas

Place this file in your dbt project: macros/get_custom_schema.sql
*/


{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ generate_schema_name_for_env(custom_schema_name, node) }}
{%- endmacro %}

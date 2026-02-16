/*
generate_database_name (default implementation)
=================================================
Controls which database dbt writes each model to.

Default behaviour:
  - If a model specifies a `database` config, use that value
  - Otherwise, use target.database

This is dbt's built-in default. You only need this file in your project
if you want to customise the logic (e.g., environment-specific database
name mapping). Otherwise dbt uses this exact logic automatically.

Reference: https://docs.getdbt.com/docs/build/custom-databases

Place this file in your dbt project: macros/get_custom_database.sql
*/


{%- macro generate_database_name(custom_database_name=none, node=none) -%}

    {%- set default_database = target.database -%}
    {%- if custom_database_name is none -%}

        {{ default_database }}

    {%- else -%}

        {{ custom_database_name | trim }}

    {%- endif -%}

{%- endmacro %}

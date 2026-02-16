/*
generate_alias_name (default implementation)
=============================================
Controls the final table/view name within the schema.

Default behaviour:
  - If a model specifies an `alias` config, use that value
  - If the model is versioned, use model_name ~ '_v' ~ version
  - Otherwise, use the model filename (node.name)

This is dbt's built-in default. You only need this file in your project
if you want to customise the logic (e.g., adding layer prefixes or
other naming conventions).

Reference: https://docs.getdbt.com/docs/build/custom-aliases

Place this file in your dbt project: macros/get_custom_alias.sql
*/


{% macro generate_alias_name(custom_alias_name=none, node=none) -%}

    {%- if custom_alias_name -%}

        {{ custom_alias_name | trim }}

    {%- elif node.version -%}

        {{ return(node.name ~ "_v" ~ (node.version | replace(".", "_"))) }}

    {%- else -%}

        {{ node.name }}

    {%- endif -%}

{%- endmacro %}

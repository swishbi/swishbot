-- macros/add_unknown_member_row.sql
-- Adds an unknown member row to a dimension model by introspecting its columns.
-- String columns get the configurable label, integers get -1, everything else gets null.
-- Set the default label in dbt_project.yml:
--   vars:
--     unknown_member_label: '*Unknown*'

{% macro add_unknown_member_row(model_name, unknown_label) %}

    {# Default the label from a project variable if not passed explicitly #}
    {%- set unknown_label = unknown_label or var('unknown_member_label', '*Unknown*') -%}
    {%- set target_relation = ref(model_name) -%}
    {%- set columns = adapter.get_columns_in_relation(target_relation) -%}

    select
        {% for column in columns %}
            {%- set dtype = column.data_type | lower -%}

            {%- if 'char' in dtype
                or 'string' in dtype
                or 'text' in dtype
                or 'varchar' in dtype
                or 'nvarchar' in dtype
                or 'nchar' in dtype
                or 'clob' in dtype -%}
                '{{ unknown_label }}' as {{ column.name }}

            {%- elif 'int' in dtype
                or 'num' in dtype
                or 'long' in dtype
                or 'short' in dtype
                or 'byte' in dtype
                or 'bigint' in dtype
                or 'smallint' in dtype
                or 'integer' in dtype -%}
                -1 as {{ column.name }}

            {%- elif 'float' in dtype
                or 'double' in dtype
                or 'real' in dtype
                or 'numeric' in dtype
                or 'decimal' in dtype
                or 'number' in dtype -%}
                null as {{ column.name }}

            {%- elif 'bool' in dtype -%}
                false as {{ column.name }}

            {%- elif 'date' in dtype
                or 'time' in dtype
                or 'timestamp' in dtype -%}
                cast(null as {{ dtype }}) as {{ column.name }}

            {%- else -%}
                null as {{ column.name }}
            {%- endif %}

            {%- if not loop.last %}, {% endif %}
        {% endfor %}

    union all

    select * from {{ ref(model_name) }}

{% endmacro %}

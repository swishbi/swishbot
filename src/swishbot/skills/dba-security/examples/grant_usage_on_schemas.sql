/*
grant_usage_on_schemas_where_select
====================================
on-run-end hook that grants USAGE on schemas where models have +grants: select.

dbt's built-in +grants only grants SELECT on individual objects — it does not
grant USAGE on the schema itself. Without USAGE, roles cannot see the schema.

This macro iterates the dbt graph, collects schemas with select grants, and
issues the appropriate platform-specific statements. Only runs in production.

Usage in dbt_project.yml:

    on-run-end:
      - "{{ grant_usage_on_schemas_where_select() }}"

Dispatches:
  - default (Snowflake): GRANT USAGE ON SCHEMA
  - postgres:            GRANT USAGE + GRANT SELECT ON ALL TABLES + ALTER DEFAULT PRIVILEGES
  - spark (Databricks):  GRANT USE SCHEMA ON SCHEMA
*/


{%- macro grant_usage_on_schemas_where_select() %}
    {{ adapter.dispatch('grant_usage_on_schemas_where_select') () }}
{%- endmacro %}


-- ==========================================================================
-- Snowflake (default)
-- ==========================================================================

{%- macro default__grant_usage_on_schemas_where_select() %}

  {%- if 'prod' in target.name %}
  {%- set schema_grants = {} %}
  {%- if execute %}
    {%- for node in graph.nodes.values() %}
      {%- set grants = node.config.get('grants') %}
      {%- set select_roles = grants['select'] if grants else [] %}
      {%- if select_roles %}
        {%- set database_schema = node.database ~ '.' ~ node.schema %}

        {%- set schema_exists_query %}
          select count(*) > 0
          from information_schema.schemata
          where lower(schema_name) = lower('{{ node.schema }}')
        {%- endset %}

        {%- set schema_exists = run_query(schema_exists_query).columns[0][0] %}
        {%- if schema_exists %}
          {%- if database_schema in schema_grants %}
            {%- do schema_grants[database_schema].update(select_roles) %}
          {%- else %}
            {%- do schema_grants.update({database_schema: set(select_roles)}) %}
          {%- endif %}
        {%- endif %}

      {%- endif %}
    {%- endfor %}
  {%- endif %}

  {%- set grant_list %}
    {%- for schema, roles in schema_grants.items() %}
      {%- for role in roles %}
        grant usage on schema {{ schema }} to {{ role }};
      {%- endfor %}
    {%- endfor %}
  {%- endset %}

  {{ return(grant_list) }}

  {%- else %}
  select 1; -- hooks will error if they don't have valid SQL in them
  {%- endif %}

{%- endmacro %}


-- ==========================================================================
-- Postgres
-- ==========================================================================
-- Postgres requires USAGE + SELECT ON ALL TABLES + DEFAULT PRIVILEGES
-- because there are no future grants at the database level.

{%- macro postgres__grant_usage_on_schemas_where_select() %}

  {%- if 'prod' in target.name %}
  {%- set schema_grants = {} %}
  {%- if execute %}
    {%- for node in graph.nodes.values() %}
      {%- set grants = node.config.get('grants') %}
      {%- set select_roles = grants['select'] if grants else [] %}
      {%- if select_roles %}
        {%- set database_schema = node.database ~ '.' ~ node.schema %}

        {%- set schema_exists_query %}
          select count(*) > 0
          from information_schema.schemata
          where lower(schema_name) = lower('{{ node.schema }}')
        {%- endset %}

        {%- set schema_exists = run_query(schema_exists_query).columns[0][0] %}
        {%- if schema_exists %}
          {%- if database_schema in schema_grants %}
            {%- do schema_grants[database_schema].update(select_roles) %}
          {%- else %}
            {%- do schema_grants.update({database_schema: set(select_roles)}) %}
          {%- endif %}
        {%- endif %}

      {%- endif %}
    {%- endfor %}
  {%- endif %}

  {%- set grant_list %}
    {%- for schema, roles in schema_grants.items() %}
      {%- for role in roles %}
        {%- set schema_name = schema.split('.')[-1] %}
        grant usage on schema {{ schema_name }} to {{ role }};
        grant select on all tables in schema {{ schema_name }} to {{ role }};
        alter default privileges in schema {{ schema_name }} grant select on tables to {{ role }};
      {%- endfor %}
    {%- endfor %}
  {%- endset %}

  {{ return(grant_list) }}

  {%- else %}
  select 1; -- hooks will error if they don't have valid SQL in them
  {%- endif %}

{%- endmacro %}


-- ==========================================================================
-- Databricks (Spark)
-- ==========================================================================
-- Databricks uses GRANT USE SCHEMA and executes grants immediately via run_query.

{%- macro spark__grant_usage_on_schemas_where_select() %}

  {%- if 'prod' in target.name %}
  {%- set schema_grants = {} %}
  {%- if execute %}
    {%- for node in graph.nodes.values() %}
      {%- set grants = node.config.get('grants') %}
      {%- set select_roles = grants['select'] if grants else [] %}
      {%- if select_roles %}
        {%- set database_schema = node.database ~ '.' ~ node.schema %}

        {%- set schema_exists_query %}
          select count(*) > 0
          from information_schema.schemata
          where lower(schema_name) = lower('{{ node.schema }}')
        {%- endset %}

        {%- set schema_exists = run_query(schema_exists_query).columns[0][0] %}
        {%- if schema_exists %}
          {%- if database_schema in schema_grants %}
            {%- do schema_grants[database_schema].update(select_roles) %}
          {%- else %}
            {%- do schema_grants.update({database_schema: set(select_roles)}) %}
          {%- endif %}
        {%- endif %}

      {%- endif %}
    {%- endfor %}
  {%- endif %}

  {%- set grant_list %}
    {%- for schema, roles in schema_grants.items() %}
      {%- for role in roles %}
        {%- set query = 'grant use schema on schema ' ~ schema ~ ' to ' ~ role ~ ';' %}
        {{ run_query(query) }}
      {%- endfor %}
    {%- endfor %}
  {%- endset %}

  {%- else %}
  select 1; -- hooks will error if they don't have valid SQL in them
  {%- endif %}

{%- endmacro %}

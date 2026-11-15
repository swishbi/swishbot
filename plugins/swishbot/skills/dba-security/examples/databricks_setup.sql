/*
Databricks (Unity Catalog) Environment Setup
==============================================
This script sets up catalogs and grants for a Databricks data warehouse
using Unity Catalog. Run these commands in the Databricks SQL editor.

Databricks maps to the security model as follows:
  - Databases      → Catalogs (raw, raw_dev, analytics, analytics_dev)
  - Schemas        → Schemas within catalogs (created at runtime by dbt/ingestion)
  - Roles          → Groups
  - Warehouses     → SQL Warehouses (managed separately in workspace settings)
  - Role hierarchy → Groups can be nested (group membership)

No schemas are created in this script — they are all created at runtime:
  - Raw schemas: created by the ingestion tool (dlt, Fivetran, etc.)
  - Analytics schemas: created by dbt (staging, intermediate, marts, etc.)

Catalog-level grants (USE SCHEMA, SELECT, etc. ON CATALOG) propagate to all
schemas and tables within the catalog. Fine-grained grants (e.g., analyst
reads only marts) are handled by dbt's +grants config and the
grant_usage_on_schemas_where_select on-run-end hook.

Service principal authentication replaces key-pair auth.

Sections:
  1. Catalogs
  2. Groups
  3. Group hierarchy
  4. Ownership grants (ALL PRIVILEGES)
  5. Read grants
*/


-- ============================================================================
-- 1. Catalogs
-- ============================================================================

CREATE CATALOG IF NOT EXISTS raw
  COMMENT 'Stores unprocessed, original data from various sources.';

CREATE CATALOG IF NOT EXISTS raw_dev
  COMMENT 'Stores unprocessed, original data from various sources for development purposes.';

CREATE CATALOG IF NOT EXISTS analytics
  COMMENT 'Contains staged, cleaned, transformed, and structured data optimized for querying and reporting.';

CREATE CATALOG IF NOT EXISTS analytics_dev
  COMMENT 'Contains development schemas for transformed data.';


-- ============================================================================
-- 2. Groups
-- ============================================================================
-- Groups are managed via Databricks account console or SCIM provisioning.
-- In practice, create these groups in the Databricks account console
-- or via Terraform/SCIM and then apply the grants below.

-- CREATE GROUP analyst;
-- CREATE GROUP developer;
-- CREATE GROUP automation;
-- CREATE GROUP loader;
-- CREATE GROUP bi;


-- ============================================================================
-- 3. Group Hierarchy
-- ============================================================================
-- Nest groups to implement role inheritance.
-- Managed in Databricks account console or via SCIM:
--
--   analyst    is a member of  developer
--   developer  is a member of  automation
--   loader     is standalone
--   bi         is standalone (read-only BI tools)
--
-- This means automation inherits all developer and analyst permissions.


-- ============================================================================
-- 4. Ownership Grants (ALL PRIVILEGES)
-- ============================================================================
-- The role that owns a catalog gets ALL PRIVILEGES — full control over
-- schemas, tables, and objects within it.

-- Loader: full control of production raw only
GRANT ALL PRIVILEGES ON CATALOG raw TO loader;

-- Developer: full control of the development catalogs. People, development
-- agents, CI and branch deployments (service principals in this group) all
-- work here; CI builds one schema per pull request in analytics_dev.
GRANT ALL PRIVILEGES ON CATALOG raw_dev TO developer;
GRANT ALL PRIVILEGES ON CATALOG analytics_dev TO developer;

-- Automation: full control of production analytics only
GRANT ALL PRIVILEGES ON CATALOG analytics TO automation;


-- ============================================================================
-- 5. Read Grants
-- ============================================================================
-- Read grants allow roles to browse, query, and execute within catalogs
-- they don't own. These propagate to all schemas and tables within.

-- Developer: read raw catalogs
GRANT USE CATALOG ON CATALOG raw TO developer;
GRANT USE SCHEMA ON CATALOG raw TO developer;
GRANT SELECT ON CATALOG raw TO developer;
GRANT BROWSE ON CATALOG raw TO developer;
GRANT EXECUTE ON CATALOG raw TO developer;
GRANT READ VOLUME ON CATALOG raw TO developer;

-- Developer: read analytics (prod) — inherited by automation
GRANT USE SCHEMA ON CATALOG analytics TO developer;
GRANT SELECT ON CATALOG analytics TO developer;
GRANT EXECUTE ON CATALOG analytics TO developer;
GRANT READ VOLUME ON CATALOG analytics TO developer;

-- Analyst: browse and use analytics catalog
-- Fine-grained SELECT (e.g., marts only) is handled by dbt's +grants
-- config and the grant_usage_on_schemas_where_select on-run-end hook.
GRANT USE CATALOG ON CATALOG analytics TO analyst;
GRANT BROWSE ON CATALOG analytics TO analyst;

-- BI: read production analytics and analytics_dev, write nothing
GRANT USE CATALOG ON CATALOG analytics TO bi;
GRANT USE SCHEMA ON CATALOG analytics TO bi;
GRANT SELECT ON CATALOG analytics TO bi;
GRANT USE CATALOG ON CATALOG analytics_dev TO bi;
GRANT USE SCHEMA ON CATALOG analytics_dev TO bi;
GRANT SELECT ON CATALOG analytics_dev TO bi;

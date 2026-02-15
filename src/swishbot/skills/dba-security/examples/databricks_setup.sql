/*
Databricks (Unity Catalog) Environment Setup
==============================================
This script sets up catalogs, schemas, groups, and grants for a Databricks
data warehouse using Unity Catalog.

Databricks maps to the security model as follows:
  - Databases      → Catalogs (raw, analytics, analytics_dev)
  - Schemas        → Schemas within catalogs
  - Roles          → Groups
  - Warehouses     → SQL Warehouses (managed separately in workspace settings)
  - Future grants  → Not supported — use MANAGED grants on catalogs/schemas
  - Role hierarchy → Groups can be nested (group membership)

Service principal authentication replaces key-pair auth.

Sections:
  1. Catalogs
  2. Schemas
  3. Groups
  4. Group hierarchy
  5. Catalog grants
  6. Schema grants
*/


-- ============================================================================
-- 1. Catalogs
-- ============================================================================
-- Catalogs provide database-level separation.

CREATE CATALOG IF NOT EXISTS raw
  COMMENT 'Stores unprocessed, original data from various sources.';

CREATE CATALOG IF NOT EXISTS raw_dev
  COMMENT 'Raw data for development purposes.';

CREATE CATALOG IF NOT EXISTS analytics
  COMMENT 'Contains staged, cleaned, transformed, and structured data.';

CREATE CATALOG IF NOT EXISTS analytics_dev
  COMMENT 'Contains development schemas for transformed data.';

-- Uncomment for CI:
-- CREATE CATALOG IF NOT EXISTS raw_ci COMMENT 'Raw data for CI environment.';
-- CREATE CATALOG IF NOT EXISTS analytics_ci COMMENT 'Transformed data for CI environment.';


-- ============================================================================
-- 2. Schemas
-- ============================================================================

-- Raw schemas are NOT created here — the ingestion tool (dlt, Fivetran, etc.)
-- creates them at runtime using the loader group's CREATE SCHEMA grant.
-- Schema names are determined by the ingestion tool (typically just the source name,
-- e.g., raw.hubspot, raw.stripe).

-- Analytics: one schema per layer
CREATE SCHEMA IF NOT EXISTS analytics.staging;
CREATE SCHEMA IF NOT EXISTS analytics.intermediate;
CREATE SCHEMA IF NOT EXISTS analytics.marts;

CREATE SCHEMA IF NOT EXISTS analytics_dev.staging;
CREATE SCHEMA IF NOT EXISTS analytics_dev.intermediate;
CREATE SCHEMA IF NOT EXISTS analytics_dev.marts;


-- ============================================================================
-- 3. Groups
-- ============================================================================
-- Groups are managed via Databricks account console or SCIM provisioning.
-- The SQL commands below document the intended group structure.
-- In practice, create these groups in the Databricks account console
-- or via Terraform/SCIM and then apply the grants below.

-- CREATE GROUP analyst;
-- CREATE GROUP developer;
-- CREATE GROUP automation;
-- CREATE GROUP loader;


-- ============================================================================
-- 4. Group Hierarchy
-- ============================================================================
-- Nest groups to implement role inheritance.
-- Managed in Databricks account console or via SCIM:
--
--   analyst    is a member of  developer
--   developer  is a member of  automation
--   loader     is standalone
--
-- This means automation inherits all developer and analyst permissions.


-- ============================================================================
-- 5. Catalog Grants
-- ============================================================================

-- Loader: use and create schemas in raw catalogs
GRANT USE CATALOG ON CATALOG raw TO loader;
GRANT CREATE SCHEMA ON CATALOG raw TO loader;
GRANT USE CATALOG ON CATALOG raw_dev TO loader;
GRANT CREATE SCHEMA ON CATALOG raw_dev TO loader;

-- Developer: read raw catalogs
GRANT USE CATALOG ON CATALOG raw TO developer;
GRANT USE CATALOG ON CATALOG raw_dev TO developer;

-- Developer: read/write analytics_dev, read analytics
GRANT USE CATALOG ON CATALOG analytics_dev TO developer;
GRANT CREATE SCHEMA ON CATALOG analytics_dev TO developer;
GRANT USE CATALOG ON CATALOG analytics TO analyst;

-- Automation: write analytics (prod)
GRANT CREATE SCHEMA ON CATALOG analytics TO automation;


-- ============================================================================
-- 6. Schema Grants
-- ============================================================================

-- Loader: raw schema grants are handled at the catalog level (CREATE SCHEMA).
-- Individual schema grants are applied after the ingestion tool creates them:
--
--   GRANT ALL PRIVILEGES ON SCHEMA raw.<source> TO loader;
--   GRANT USE SCHEMA ON SCHEMA raw.<source> TO developer;
--   GRANT SELECT ON SCHEMA raw.<source> TO developer;

-- Developer: read all analytics (prod) schemas

-- Developer: read/write analytics_dev schemas
GRANT ALL PRIVILEGES ON SCHEMA analytics_dev.staging TO developer;
GRANT ALL PRIVILEGES ON SCHEMA analytics_dev.intermediate TO developer;
GRANT ALL PRIVILEGES ON SCHEMA analytics_dev.marts TO developer;

-- Developer: read analytics (prod) schemas
GRANT USE SCHEMA ON SCHEMA analytics.staging TO developer;
GRANT SELECT ON SCHEMA analytics.staging TO developer;
GRANT USE SCHEMA ON SCHEMA analytics.intermediate TO developer;
GRANT SELECT ON SCHEMA analytics.intermediate TO developer;
GRANT USE SCHEMA ON SCHEMA analytics.marts TO developer;
GRANT SELECT ON SCHEMA analytics.marts TO developer;

-- Analyst: read marts only
GRANT USE SCHEMA ON SCHEMA analytics.marts TO analyst;
GRANT SELECT ON SCHEMA analytics.marts TO analyst;

-- Automation: full access to analytics (prod) schemas
GRANT ALL PRIVILEGES ON SCHEMA analytics.staging TO automation;
GRANT ALL PRIVILEGES ON SCHEMA analytics.intermediate TO automation;
GRANT ALL PRIVILEGES ON SCHEMA analytics.marts TO automation;

/*
DuckDB Environment Setup
=========================
This script sets up schemas for a DuckDB data warehouse.

DuckDB limitations:
  - Single-user, embedded database — no built-in roles or user management
  - No GRANT/REVOKE — access is controlled by who can open the database file
  - No separate compute — all queries run in the same process
  - No environment separation at the database level

Despite these limitations, DuckDB should follow the same schema naming
conventions so that dbt projects and SQL patterns are portable across
platforms. The security boundary is the file system: control who can
access the .duckdb file(s).

Strategies for environment separation:
  - Use separate .duckdb files for raw vs analytics (raw.duckdb, analytics.duckdb)
  - Attach both databases in a single session for cross-database queries
  - Use separate files per environment (analytics_dev.duckdb, analytics.duckdb)

Sections:
  1. Schema setup (single database)
  2. Multi-database setup (attached databases)
*/


-- ============================================================================
-- 1. Schema Setup (Single Database)
-- ============================================================================
-- When using a single DuckDB file, use schemas to separate layers.
-- This is the simplest approach for local development.

-- Raw schemas are NOT created here — the ingestion tool (dlt, Fivetran, etc.)
-- creates them at runtime. Schema names are determined by the ingestion tool,
-- typically just the source name (e.g., hubspot, stripe) or raw_<source>
-- depending on the platform convention.

-- Analytics layers
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS marts;

-- Developer schema (for dbt development)
-- CREATE SCHEMA IF NOT EXISTS dbt_jsmith;


-- ============================================================================
-- 2. Multi-Database Setup (Attached Databases)
-- ============================================================================
-- For closer parity with Snowflake/Databricks, use separate .duckdb files
-- and attach them in a single session. This gives you physical separation
-- of raw and analytics data.

-- Create or attach the raw database
-- Raw schemas are created by the ingestion tool at runtime.
-- ATTACH 'raw.duckdb' AS raw;

-- Create or attach the analytics database
-- ATTACH 'analytics.duckdb' AS analytics;
-- CREATE SCHEMA IF NOT EXISTS analytics.staging;
-- CREATE SCHEMA IF NOT EXISTS analytics.intermediate;
-- CREATE SCHEMA IF NOT EXISTS analytics.marts;

-- Create or attach the dev database
-- ATTACH 'analytics_dev.duckdb' AS analytics_dev;
-- CREATE SCHEMA IF NOT EXISTS analytics_dev.staging;
-- CREATE SCHEMA IF NOT EXISTS analytics_dev.intermediate;
-- CREATE SCHEMA IF NOT EXISTS analytics_dev.marts;
-- CREATE SCHEMA IF NOT EXISTS analytics_dev.dbt_jsmith;

-- Query across databases:
-- SELECT * FROM raw.hubspot.contacts;
-- SELECT * FROM analytics.marts.dim_customers;

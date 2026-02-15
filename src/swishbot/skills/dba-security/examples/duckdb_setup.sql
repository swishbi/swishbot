/*
DuckDB Environment Setup
=========================
DuckDB is a single-user, embedded database with no built-in roles, grants,
or user management. There is no setup script in the traditional sense.

This file documents the conventions and strategies for maintaining
consistency with the security model so that dbt projects and SQL patterns
are portable across platforms.

DuckDB limitations:
  - No GRANT/REVOKE — access is controlled by who can open the database file
  - No separate compute — all queries run in the same process
  - No environment separation at the database level (unless using ATTACH)

The security boundary is the file system: control who can access the
.duckdb file(s).

Sections:
  1. Schema conventions (single database)
  2. Multi-database setup (attached databases)
*/


-- ============================================================================
-- 1. Schema Conventions (Single Database)
-- ============================================================================
-- When using a single DuckDB file, use schemas to separate layers.
-- This is the simplest approach for local development.
--
-- No schemas are pre-created — they are all created at runtime:
--   - Raw schemas: created by the ingestion tool (e.g., hubspot, stripe)
--   - Analytics schemas: created by dbt (staging, intermediate, marts)
--   - Developer schemas: created by dbt (dbt_jsmith, etc.)
--
-- DuckDB creates schemas automatically when dbt runs, so no setup is needed.


-- ============================================================================
-- 2. Multi-Database Setup (Attached Databases)
-- ============================================================================
-- For closer parity with Snowflake/Databricks, use separate .duckdb files
-- and attach them in a single session. This gives you physical separation
-- of raw and analytics data.
--
-- All schemas within each database are created at runtime by the ingestion
-- tool or dbt — no need to pre-create them.

-- ATTACH 'raw.duckdb' AS raw;
-- ATTACH 'analytics.duckdb' AS analytics;
-- ATTACH 'analytics_dev.duckdb' AS analytics_dev;

-- Query across databases:
-- SELECT * FROM raw.hubspot.contacts;
-- SELECT * FROM analytics.marts.dim_customers;

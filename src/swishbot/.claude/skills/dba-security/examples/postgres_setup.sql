/*
Postgres Environment Setup
===========================
This script sets up roles, users, and database-level grants for a Postgres
data warehouse. All schemas live in a single database (Postgres does not
support cross-database queries, so dbt cannot reference a separate raw database).

Postgres limitations:
  - No cross-database queries — all schemas live in a single database
  - No future grants on schemas — use ALTER DEFAULT PRIVILEGES to approximate
  - No dedicated compute per role — all roles share the same server
  - No key-pair auth — service users use passwords (rotate regularly)

No schemas are created in this script — they are all created at runtime:
  - Raw schemas: created by the ingestion tool (dlt, Fivetran, etc.)
    using the naming convention raw_<source> (e.g., raw_hubspot, raw_stripe)
  - Analytics schemas: created by dbt (staging, intermediate, marts, etc.)
  - Developer schemas: created by dbt (dbt_jsmith, etc.)

The order of operations problem:
  Postgres has no equivalent of Snowflake's future grants on schemas. You can't
  grant USAGE ON SCHEMA before the schema exists. This script uses two strategies:

  1. ALTER DEFAULT PRIVILEGES (without IN SCHEMA) — applies to all future tables
     created by a role in ANY schema. Handles SELECT grants automatically.

  2. dbt's on-run-end hook (grant_usage_on_schemas_where_select) — grants USAGE
     on schemas after dbt creates them. Handles schema-level access at runtime.

  Together, these cover the gap: DEFAULT PRIVILEGES handles table-level SELECT,
  and the on-run-end hook handles schema-level USAGE.

Ownership note:
  In Postgres, the role that creates an object owns it. A role can only DROP
  objects it owns. This is not an issue with the environment separation model:
  - Developer creates schemas in analytics_dev → developer owns them
  - Automation creates schemas in analytics → automation owns them
  The roles never cross paths in the same schema, so ownership stays clean.

Sections:
  1. Roles (group roles)
  2. Users (login roles)
  3. Role hierarchy
  4. Database grants
  5. Default privileges
*/


-- ============================================================================
-- 1. Roles (Group Roles)
-- ============================================================================
-- NOLOGIN roles act as permission groups. Human users and service users
-- are granted these roles to inherit their permissions.

CREATE ROLE analyst;
COMMENT ON ROLE analyst IS 'Analyst role — read access to analytics marts.';

CREATE ROLE developer;
COMMENT ON ROLE developer IS 'Developer role — read raw and analytics, write dev schemas.';

CREATE ROLE automation;
COMMENT ON ROLE automation IS 'Automation role — read raw, write all analytics schemas.';

CREATE ROLE loader;
COMMENT ON ROLE loader IS 'Loader role — read/write raw schemas.';


-- ============================================================================
-- 2. Users (Login Roles)
-- ============================================================================
-- CREATE USER is equivalent to CREATE ROLE with LOGIN.
-- Change passwords immediately after running this script.

CREATE USER loader_user WITH PASSWORD 'changeme';
CREATE USER automation_user WITH PASSWORD 'changeme';

-- ALTER USER loader_user WITH PASSWORD '<secure password>';
-- ALTER USER automation_user WITH PASSWORD '<secure password>';

-- Grant group roles to service users
GRANT loader TO loader_user;
GRANT automation TO automation_user;

-- Human developers get the developer role
-- CREATE USER jsmith WITH PASSWORD '...';
-- GRANT developer TO jsmith;


-- ============================================================================
-- 3. Role Hierarchy
-- ============================================================================
-- Analyst < Developer < Automation (with inheritance)
-- Loader is standalone

GRANT analyst TO developer;
GRANT developer TO automation;


-- ============================================================================
-- 4. Database Grants
-- ============================================================================
-- CONNECT controls who can connect to the database.
-- CREATE controls who can create schemas at runtime.
-- The loader creates raw schemas; automation creates analytics schemas;
-- developers create their own dbt_<name> schemas.
-- NOTE: Replace <database_name> with the actual database name before running.

GRANT CONNECT ON DATABASE <database_name> TO loader;
GRANT CONNECT ON DATABASE <database_name> TO developer;
GRANT CONNECT ON DATABASE <database_name> TO analyst;

GRANT CREATE ON DATABASE <database_name> TO loader;
GRANT CREATE ON DATABASE <database_name> TO developer;
GRANT CREATE ON DATABASE <database_name> TO automation;


-- ============================================================================
-- 5. Default Privileges
-- ============================================================================
-- ALTER DEFAULT PRIVILEGES without IN SCHEMA applies to ALL future tables
-- created by the specified role, regardless of which schema they're in.
-- This is Postgres's closest equivalent to Snowflake's future grants.
--
-- Schema-level USAGE grants cannot be set in advance — those are handled
-- by dbt's grant_usage_on_schemas_where_select on-run-end hook.

-- Tables created by loader (in any schema) are readable by developer
ALTER DEFAULT PRIVILEGES FOR ROLE loader
  GRANT SELECT ON TABLES TO developer;

-- Tables created by automation (in any schema) are readable by developer
ALTER DEFAULT PRIVILEGES FOR ROLE automation
  GRANT SELECT ON TABLES TO developer;

-- Tables created by developer (in any schema) are readable by other developers
ALTER DEFAULT PRIVILEGES FOR ROLE developer
  GRANT SELECT ON TABLES TO developer;

-- Analyst grants are NOT set here — they are managed by dbt's +grants config
-- which grants SELECT only on marts models, and the on-run-end hook which
-- grants USAGE on the marts schema. This keeps analyst access scoped to
-- exactly the models that dbt declares, rather than broad database-level access.

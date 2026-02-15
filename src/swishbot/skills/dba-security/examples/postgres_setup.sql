/*
Postgres Environment Setup
===========================
This script sets up roles, schemas, and grants for a Postgres data warehouse.

Postgres limitations:
  - No cross-database queries — all schemas live in a single database
  - No future grants — must re-run grants when new tables are created
    (use default privileges to approximate future grants)
  - No dedicated compute per role — all roles share the same server

The schema naming convention encodes the layer separation that Snowflake
achieves with separate databases:
  - raw_<source>   → raw layer (one schema per source system)
  - staging        → staging/bronze layer
  - intermediate   → intermediate/silver layer
  - marts          → marts/gold layer

Sections:
  1. Roles
  2. Role hierarchy
  3. Schemas
  4. Schema grants
  5. Default privileges (approximates future grants)
  6. Developer schema creation
*/


-- ============================================================================
-- 1. Roles
-- ============================================================================
-- Postgres roles double as both users and groups.
-- NOLOGIN roles act as groups; LOGIN roles act as service/human users.

-- Group roles (no login)
CREATE ROLE analyst NOLOGIN;
COMMENT ON ROLE analyst IS 'Analyst role — read access to marts schemas.';

CREATE ROLE developer NOLOGIN;
COMMENT ON ROLE developer IS 'Developer role — read raw and analytics, write dev schemas.';

CREATE ROLE automation NOLOGIN;
COMMENT ON ROLE automation IS 'Automation role — read raw, write all analytics schemas.';

CREATE ROLE loader NOLOGIN;
COMMENT ON ROLE loader IS 'Loader role — read/write raw schemas.';

-- Service users (login)
CREATE ROLE loader_svc LOGIN;
COMMENT ON ROLE loader_svc IS 'Service user for data loading (dlt, Fivetran, etc).';

CREATE ROLE automation_svc LOGIN;
COMMENT ON ROLE automation_svc IS 'Service user for dbt CI/CD automation.';


-- ============================================================================
-- 2. Role Hierarchy
-- ============================================================================
-- Analyst < Developer < Automation (with inheritance)
-- Loader is standalone

GRANT analyst TO developer;
GRANT developer TO automation;

-- Assign group roles to service users
GRANT loader TO loader_svc;
GRANT automation TO automation_svc;

-- Human developers get the developer role
-- GRANT developer TO <username>;


-- ============================================================================
-- 3. Schemas
-- ============================================================================
-- Raw layer: one schema per source system
-- Transformed layers: one schema per layer
-- Dev schemas: created per developer (see section 6)

-- Raw schemas are NOT created here — the ingestion tool (dlt, Fivetran, etc.)
-- creates them at runtime using the loader role's CREATE permission.
-- In Postgres, raw schemas use the naming convention: raw_<source>
-- (e.g., raw_hubspot, raw_stripe)

-- Analytics schemas
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS marts;

-- Dev schema (shared development space)
CREATE SCHEMA IF NOT EXISTS dev;


-- ============================================================================
-- 4. Schema Grants
-- ============================================================================

-- Loader: create schemas in the database (raw schemas created by ingestion tool)
-- In Postgres, there is no CREATE SCHEMA ON DATABASE — the loader role must own
-- or have the CREATEDB privilege, or you grant schema creation via:
GRANT CREATE ON DATABASE current_database TO loader;

-- NOTE: After the loader creates a raw schema (e.g., raw_hubspot), you must grant
-- read access to the developer role. This can be scripted or run manually:
--
--   GRANT USAGE ON SCHEMA raw_<source> TO developer;
--   GRANT SELECT ON ALL TABLES IN SCHEMA raw_<source> TO developer;
--   ALTER DEFAULT PRIVILEGES FOR ROLE loader IN SCHEMA raw_<source>
--     GRANT SELECT ON TABLES TO developer;

-- Developer: read all analytics schemas
GRANT USAGE ON SCHEMA staging TO developer;
GRANT SELECT ON ALL TABLES IN SCHEMA staging TO developer;
GRANT USAGE ON SCHEMA intermediate TO developer;
GRANT SELECT ON ALL TABLES IN SCHEMA intermediate TO developer;
GRANT USAGE ON SCHEMA marts TO developer;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO developer;

-- Developer: read/write dev schema
GRANT USAGE, CREATE ON SCHEMA dev TO developer;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dev TO developer;

-- Analyst: read marts only
GRANT USAGE ON SCHEMA marts TO analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO analyst;

-- Automation: read/write all analytics schemas
GRANT USAGE, CREATE ON SCHEMA staging TO automation;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO automation;
GRANT USAGE, CREATE ON SCHEMA intermediate TO automation;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA intermediate TO automation;
GRANT USAGE, CREATE ON SCHEMA marts TO automation;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA marts TO automation;


-- ============================================================================
-- 5. Default Privileges (approximates future grants)
-- ============================================================================
-- Default privileges apply to objects created by a specific role in the future.
-- Run these for each role that creates objects so that other roles can read them.

-- NOTE: Default privileges for raw schemas must be set after the loader
-- creates each schema. See the grant notes in section 4 above.

-- Tables created by automation in analytics schemas are readable by developer
ALTER DEFAULT PRIVILEGES FOR ROLE automation IN SCHEMA staging
  GRANT SELECT ON TABLES TO developer;
ALTER DEFAULT PRIVILEGES FOR ROLE automation IN SCHEMA intermediate
  GRANT SELECT ON TABLES TO developer;
ALTER DEFAULT PRIVILEGES FOR ROLE automation IN SCHEMA marts
  GRANT SELECT ON TABLES TO developer;

-- Tables created by automation in marts are readable by analyst
ALTER DEFAULT PRIVILEGES FOR ROLE automation IN SCHEMA marts
  GRANT SELECT ON TABLES TO analyst;

-- Tables created by developer in dev schema are readable by other developers
ALTER DEFAULT PRIVILEGES FOR ROLE developer IN SCHEMA dev
  GRANT SELECT ON TABLES TO developer;


-- ============================================================================
-- 6. Developer Schema Creation
-- ============================================================================
-- In Postgres, developers share the `dev` schema rather than creating
-- individual schemas (dbt_jsmith, etc). If you prefer per-developer schemas,
-- create them manually and grant accordingly:
--
-- CREATE SCHEMA dbt_jsmith;
-- GRANT USAGE, CREATE ON SCHEMA dbt_jsmith TO developer;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dbt_jsmith TO developer;
-- ALTER DEFAULT PRIVILEGES FOR ROLE developer IN SCHEMA dbt_jsmith
--   GRANT SELECT ON TABLES TO developer;

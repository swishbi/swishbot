/*
Snowflake Environment Setup
============================
This script sets up the complete Snowflake environment for the data warehouse.
Run these commands in the Snowflake UI with ACCOUNTADMIN access.

WARNING: CREATE OR REPLACE statements will overwrite existing objects.

Sections:
  1. Account settings
  2. Roles
  3. Service users
  4. Role hierarchy
  5. Warehouses
  6. Databases
  7. Warehouse grants
  8. Database grants
  9. Future grants
*/


-- ============================================================================
-- 1. Account Settings
-- ============================================================================

use role accountadmin;

-- Allow admin roles to use the default warehouse
grant usage on warehouse COMPUTE_WH to role SYSADMIN;
grant usage on warehouse COMPUTE_WH to role USERADMIN;

-- Case-insensitive identifiers (recommended for dbt compatibility)
alter account set QUOTED_IDENTIFIERS_IGNORE_CASE = TRUE;

-- Allow MFA caching for smoother developer experience
alter account set ALLOW_CLIENT_MFA_CACHING = TRUE;

-- Authentication policy: allow Personal Access Tokens from any IP
-- Used for automation and CI/CD service users
create authentication policy auth_pol_allow_pat_all_ips
  PAT_POLICY = (
    NETWORK_POLICY_EVALUATION = ENFORCED_NOT_REQUIRED
  )
  comment = 'Allows Personal Access Token login from any IP address (no network policy enforced). Intended for use with automation or CI/CD.';
alter account set authentication policy auth_pol_allow_pat_all_ips;


-- ============================================================================
-- 2. Roles
-- ============================================================================

use role useradmin;

create or replace role ANALYST
  comment = 'Analyst role can read data in analytics.marts.';

create or replace role DEVELOPER
  comment = 'Developer role can read data in raw and analytics, and write data in analytics_dev.';

create or replace role AUTOMATION
  comment = 'Automation role can read data in raw and write data in analytics.';

create or replace role LOADER
  comment = 'Loader role can read and write data in raw.';


-- ============================================================================
-- 3. Service Users
-- ============================================================================
-- Service users use key-pair auth (not passwords).
-- Generate a key pair: openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
-- Extract public key:  openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

create or replace user LOADER with
    default_role = LOADER
    type = 'SERVICE'
    rsa_public_key = 'MIIBIjANBgkqh...';  -- replace with actual public key

create or replace user AUTOMATION with
    default_role = AUTOMATION
    type = 'SERVICE'
    rsa_public_key = 'MIIBIjANBgkqh...';  -- replace with actual public key

grant role LOADER to user LOADER;
grant role AUTOMATION to user AUTOMATION;


-- ============================================================================
-- 4. Role Hierarchy
-- ============================================================================
-- Analyst < Developer < Automation (with inheritance)
-- Loader is standalone (no inheritance into the analyst chain)
-- Both top-level roles roll up to SYSADMIN for admin visibility

grant role ANALYST to role DEVELOPER;
grant role DEVELOPER to role AUTOMATION;
grant role AUTOMATION to role SYSADMIN;
grant role LOADER to role SYSADMIN;


-- ============================================================================
-- 5. Warehouses
-- ============================================================================
-- Each role gets its own compute warehouse for cost isolation and monitoring.

use role sysadmin;

create or replace warehouse ANALYST_WH with
    warehouse_size = 'XSMALL'
    initially_suspended = true
    auto_suspend = 600
    auto_resume = true;

create or replace warehouse DEVELOPER_WH with
    warehouse_size = 'XSMALL'
    initially_suspended = true
    auto_suspend = 600
    auto_resume = true;

create or replace warehouse AUTOMATION_WH with
    warehouse_size = 'XSMALL'
    initially_suspended = true
    auto_suspend = 600
    auto_resume = true;

create or replace warehouse LOADER_WH with
    warehouse_size = 'XSMALL'
    initially_suspended = true
    auto_suspend = 600
    auto_resume = true;


-- ============================================================================
-- 6. Databases
-- ============================================================================

create or replace database RAW
  comment = 'Stores unprocessed, original data from various sources.';

create or replace database RAW_DEV
  comment = 'Stores unprocessed, original data from various sources for development purposes.';

create or replace database ANALYTICS
  comment = 'Contains staged, cleaned, transformed, and structured data optimized for querying and reporting.';

create or replace database ANALYTICS_DEV
  comment = 'Contains development schemas for transformed data.';

create or replace database ANALYTICS_CI
  comment = 'Transformed data for CI environment. CI reads raw from production.';


-- ============================================================================
-- 7. Warehouse Grants
-- ============================================================================

use role securityadmin;

grant usage on warehouse LOADER_WH to role LOADER;
grant usage on warehouse ANALYST_WH to role ANALYST;
grant usage on warehouse DEVELOPER_WH to role DEVELOPER;
grant usage on warehouse AUTOMATION_WH to role AUTOMATION;


-- ============================================================================
-- 8. Database Grants
-- ============================================================================

-- Loader: read/write raw databases
grant usage on database RAW to role LOADER;
grant usage on database RAW_DEV to role LOADER;
grant create schema on database RAW to role LOADER;
grant create schema on database RAW_DEV to role LOADER;

-- Developer: read raw, read/write analytics_dev, read analytics
grant usage on database RAW to role DEVELOPER;
grant usage on database RAW_DEV to role DEVELOPER;
grant usage on database ANALYTICS_DEV to role DEVELOPER;
grant usage on database ANALYTICS to role DEVELOPER;
grant usage on database ANALYTICS to role ANALYST;
grant create schema on database ANALYTICS_DEV to role DEVELOPER;

-- Automation: write analytics (prod and CI)
grant create schema on database ANALYTICS to role AUTOMATION;
grant usage on database ANALYTICS_CI to role AUTOMATION;
grant create schema on database ANALYTICS_CI to role AUTOMATION;


-- ============================================================================
-- 9. Future Grants
-- ============================================================================
-- Future grants ensure new schemas and tables automatically inherit permissions.
-- No schemas are created in this script — they are all created at runtime:
--   - Raw schemas: created by the ingestion tool (dlt, Fivetran, etc.)
--   - Analytics schemas: created by dbt (staging, intermediate, marts, etc.)
--
-- Future grants handle the broad read access (developer can read everything).
-- Fine-grained grants (e.g., analyst reads only marts) are handled by dbt's
-- +grants config and the grant_usage_on_schemas_where_select on-run-end hook.

-- Developer can read all raw data
grant usage on future schemas in database RAW to role DEVELOPER;
grant select on future tables in database RAW to role DEVELOPER;
grant usage on future schemas in database RAW_DEV to role DEVELOPER;
grant select on future tables in database RAW_DEV to role DEVELOPER;

-- Developer can read/write analytics_dev
grant usage on future schemas in database ANALYTICS_DEV to role DEVELOPER;
grant select on future tables in database ANALYTICS_DEV to role DEVELOPER;
grant select on future views in database ANALYTICS_DEV to role DEVELOPER;

-- Developer (and inherited by Automation) can read analytics
grant usage on future schemas in database ANALYTICS to role DEVELOPER;
grant select on future tables in database ANALYTICS to role DEVELOPER;
grant select on future views in database ANALYTICS to role DEVELOPER;

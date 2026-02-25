# Setup Warehouse Security

Configure database separation, environments, roles, and platform-specific security from scratch.

## Step 1: Create Database Separation

Split raw and transformed data into **separate databases**: `raw` and `analytics`.

**Rationale:** The raw layer may contain sensitive PII/PHI that most users should never see. Separate databases make access controls simpler — you can grant or deny access at the database level rather than managing schema-by-schema permissions.

| Platform | Separation approach |
|----------|-------------------|
| **Snowflake** | Full support — separate databases (`RAW`, `ANALYTICS`) |
| **Databricks** | Catalog separation (Unity Catalog) |
| **BigQuery** | Separate projects or datasets |
| **Postgres** | Schemas only — no cross-database queries in dbt, so use schema-level grants |
| **DuckDB** | Single-database typically — use schema separation |

On platforms that don't support cross-database queries (Postgres, DuckDB), apply the same logical separation using schemas and enforce access via schema-level grants. The security model stays the same even when the physical separation differs.

## Step 2: Create Environment Databases

Create environment-specific databases to isolate where each process **writes**. Reads flow differently — CI and development both read from production raw, avoiding the need to clone or duplicate source data.

| Database | Purpose | Who writes | Who reads |
|----------|---------|------------|-----------|
| **`raw`** | Production source data | Loader | Developer, Automation |
| **`raw_dev`** | Pipeline development sandbox | Loader (during testing) | Developer |
| **`analytics`** | Production transformations | Automation | Developer, Analyst |
| **`analytics_ci`** | CI test transformations | Automation | Automation |
| **`analytics_dev`** | Developer workspaces | Developer | Developer |

Key principles:

- **No `raw_ci` database.** CI tests transformations, not ingestion — it reads source data from production `raw` and writes results to `analytics_ci`. This avoids cloning large raw datasets into CI.
- **`raw_dev` is ephemeral.** It exists for testing new pipelines during development. Once a pipeline is promoted to production, the `raw_dev` data for that source is stale and disposable.
- **CI and production analytics** are only touched by automation — never by humans directly
- **Development** gives developers write access to `analytics_dev` and read access to production `raw` and `analytics`
- **dbt developer schemas** live in `analytics_dev` using the pattern `dbt_<first-initial><lastname>` (e.g., `dbt_jsmith`)

## Step 3: Create Roles and Hierarchy

Four core roles with a clear inheritance hierarchy:

```
Loader (standalone)

Analyst < Developer < Automation
```

| Role | Purpose |
|------|---------|
| **Loader** | Standalone role (no inheritance). Reads and writes to raw databases (`raw`, `raw_dev`). Used by ingestion services (dlt, Fivetran, etc.) |
| **Analyst** | Read-only access to analytics marts layer. Starting point for business users |
| **Developer** | Inherits Analyst. Plus: read `raw` and `raw_dev`, read/write `analytics_dev`, read production `analytics` |
| **Automation** | Inherits Developer. Plus: read/write `analytics` and `analytics_ci`, create schemas. Used by dbt CI/CD |

### Role Permissions Summary

| Role | `raw` | `raw_dev` | `analytics` | `analytics_dev` | `analytics_ci` |
|------|-------|-----------|-------------|-----------------|----------------|
| **Loader** | read/write | read/write | — | — | — |
| **Analyst** | — | — | read (marts only) | — | — |
| **Developer** | read | read | read | read/write + create schema | — |
| **Automation** | read | — | read/write + create schema | — | read/write + create schema |

### Growing the Analyst Role

As marts expand into domain-specific schemas, create additional analyst roles scoped to specific domains:

- `finance_analyst` → read access to `mrt_finance` only
- `marketing_analyst` → read access to `mrt_marketing` only

### Service Users & Compute (Snowflake-Specific)

- Each role gets its own compute warehouse (e.g., `LOADER_WH`, `ANALYST_WH`, `DEVELOPER_WH`, `AUTOMATION_WH`)
- Service users (`loader`, `automation`) use **key-pair authentication**, not passwords
- Service users are created with `type = 'SERVICE'`

## Step 4: Run Platform-Specific Setup Script

See the examples directory for complete reference scripts:

- [`examples/snowflake_setup.sql`](../examples/snowflake_setup.sql) — Full Snowflake setup
- [`examples/databricks_setup.sql`](../examples/databricks_setup.sql) — Databricks/Unity Catalog setup
- [`examples/bigquery_setup.sh`](../examples/bigquery_setup.sh) — BigQuery/GCP setup
- [`examples/postgres_setup.sql`](../examples/postgres_setup.sql) — Postgres setup
- [`examples/duckdb_setup.sql`](../examples/duckdb_setup.sql) — DuckDB setup

### Source Promotion Workflow

1. **Pipeline development** — Loader writes test extractions to `raw_dev`. Developer builds staging models against `raw_dev` using a source database var override
2. **First production deploy** — Run a full backfill into `raw` (prod). Remove the source database var override so dbt reads from `raw`
3. **Ongoing transformation changes** — CI and dev both read from `raw` (prod) directly. No cloning needed — dbt profiles and source vars control which raw database is read

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

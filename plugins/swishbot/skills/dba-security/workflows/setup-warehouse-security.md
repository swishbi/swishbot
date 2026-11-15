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
| **`raw_dev`** | Pipeline development sandbox | Developer (people, agents, CI and branch deployments) | Developer |
| **`analytics`** | Production transformations | Automation | Developer, Analyst, BI |
| **`analytics_dev`** | Developer workspaces and CI | Developer (people, agents and CI) | Developer, BI |

Key principles:

- **No CI databases.** CI tests transformations, not ingestion. It reads source data from production `raw` and writes results to a schema per pull request in `analytics_dev` (`dbt_ci_pr_<number>`). This avoids cloning large raw datasets into CI.
- **`raw_dev` is ephemeral.** It exists for testing new pipelines during development. Once a pipeline is promoted to production, the `raw_dev` data for that source is stale and disposable.
- **Production `analytics`** is only written by Automation: never by people, agents or CI
- **CI runs untrusted code.** A pull request can carry a bad change, a malicious dependency or an AI agent's mistake, and CI runs it. So CI signs in as its own user on Developer: it reads production (for `--defer`) and writes only the development databases
- **Development** gives developers write access to `raw_dev` and `analytics_dev` and read access to production `raw` and `analytics`
- **`raw_dev` belongs to development.** Loader writes production `raw` only. Every object is owned by the role that created it, and changing a table (dlt adds columns as a source grows) takes ownership. So a `raw_dev` schema created by Loader stays out of developers' reach. Keep Loader out of `raw_dev` entirely
- **dbt developer schemas** live in `analytics_dev` using the pattern `dbt_<first-initial><lastname>` (e.g., `dbt_jsmith`)

## Step 3: Create Roles and Hierarchy

Five core roles with a clear inheritance hierarchy:

```
Loader (standalone)
BI (standalone)

Analyst < Developer < Automation
```

| Role | Purpose |
|------|---------|
| **Loader** | Standalone role (no inheritance). Reads and writes production `raw`. Used by production ingestion only (dlt, Fivetran, etc.) |
| **Analyst** | Read-only access to analytics marts layer. Starting point for business users |
| **BI** | Standalone, read-only. Reads production `analytics` and `analytics_dev`. Used by BI tools and semantic layers (Power BI, Cube), one user per tool |
| **Developer** | Inherits Analyst. Plus: read `raw` and production `analytics`, read/write `raw_dev` and `analytics_dev`. Used by people, development agents and dbt CI |
| **Automation** | Inherits Developer. Plus: read/write production `analytics`, create schemas. Used by production dbt runs only |

### Role Permissions Summary

| Role | `raw` | `raw_dev` | `analytics` | `analytics_dev` |
|------|-------|-----------|-------------|-----------------|
| **Loader** | read/write | — | — | — |
| **Analyst** | — | — | read (marts only) | — |
| **BI** | — | — | read | read |
| **Developer** | read | read/write + create schema | read | read/write + create schema |
| **Automation** | read | read/write (inherited) | read/write + create schema | read/write (inherited) |

### Growing the Analyst Role

As marts expand into domain-specific schemas, create additional analyst roles scoped to specific domains:

- `finance_analyst` → read access to `mrt_finance` only
- `marketing_analyst` → read access to `mrt_marketing` only

### Users: Who, Not What

Roles say what a login may do; users say who it is. Give every person, service, tool and agent its own user on the role that fits its job, so query history shows who ran what while access stays defined in the roles:

| User | Role | Signs in with |
|------|------|---------------|
| `loader` | Loader | key pair |
| `automation` | Automation | key pair |
| `dbt_ci`, for dbt CI and Dagster branch deployments (both run pull request code) | Developer | key pair |
| one per BI tool (`powerbi`, `cube`) | BI | key pair |
| one per development agent | Developer | programmatic access token restricted to Developer |

### Service Users & Compute (Snowflake-Specific)

- Each role gets its own compute warehouse (e.g., `LOADER_WH`, `ANALYST_WH`, `DEVELOPER_WH`, `AUTOMATION_WH`, `BI_WH`)
- Service users use **key-pair authentication**, not passwords. A development agent's programmatic access token is restricted to the Developer role
- Service users are created with `type = 'SERVICE'`

## Step 4: Run Platform-Specific Setup Script

See the examples directory for complete reference scripts:

- [`examples/snowflake_setup.sql`](../examples/snowflake_setup.sql) — Full Snowflake setup
- [`examples/databricks_setup.sql`](../examples/databricks_setup.sql) — Databricks/Unity Catalog setup
- [`examples/bigquery_setup.sh`](../examples/bigquery_setup.sh) — BigQuery/GCP setup
- [`examples/postgres_setup.sql`](../examples/postgres_setup.sql) — Postgres setup
- [`examples/duckdb_setup.sql`](../examples/duckdb_setup.sql) — DuckDB setup

### Source Promotion Workflow

1. **Pipeline development** — A developer, person or agent, loads test extractions into `raw_dev` and builds staging models against them using a source database var override
2. **First production deploy** — Run a full backfill into `raw` (prod). Remove the source database var override so dbt reads from `raw`
3. **Ongoing transformation changes** — CI and dev both read from `raw` (prod) directly. No cloning needed — dbt profiles and source vars control which raw database is read

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

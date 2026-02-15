---
name: dba-security
description: "Apply DBA security best practices. Use when configuring warehouse roles, access controls, row-level security, data masking, or audit policies."
---

# DBA Security Practices

## Overview

Security is about **separation** — separate layers, databases, environments, and roles. The goal is to limit blast radius and enforce least-privilege access at every level of the warehouse.

The warehouse is organised into 4 layers:

| Layer | Purpose | Schema pattern |
|-------|---------|----------------|
| **Raw** | Unprocessed source data | One schema per source system, created at runtime by the ingestion tool (e.g., `hubspot`, `stripe`) |
| **Staging (bronze)** | First transformation layer — clean, rename, type | `staging` schema |
| **Intermediate (silver)** | Business logic joins and enrichment | `intermediate` schema |
| **Marts (gold)** | Consumer-facing analytical models | `marts` schema (split later as complexity grows) |

Raw schema names are determined by the ingestion tool (dlt, Fivetran, Airbyte, etc.) — typically just the source name (e.g., `hubspot`, `stripe`). The setup scripts grant `CREATE SCHEMA` to the loader role so the ingestion tool can create these at runtime. Do not pre-create raw schemas in the setup scripts.

As mart complexity grows, split into domain-specific schemas (e.g., `mrt_finance`, `mrt_marketing`). This also enables fine-grained analyst roles per domain.

## Database Separation Strategy

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

## Environment Strategy

Create environment-specific databases to isolate development, CI, and production:

| Environment | Raw database | Analytics database | Who writes |
|-------------|-------------|-------------------|------------|
| **Production** | `raw` | `analytics` | Loader (raw), Automation (analytics) |
| **CI** | `raw_ci` | `analytics_ci` | Automation only |
| **Development** | `raw_dev` | `analytics_dev` | Loader (raw_dev), Developers (analytics_dev) |

- **CI and production** are only touched by automation/devops processes — never by humans directly
- **Development** gives developers write access to `analytics_dev` and read access to CI and production
- **dbt developer schemas** live in `analytics_dev` using the pattern `dbt_<first-initial><lastname>` (e.g., `dbt_jsmith`). Developers can create their own schemas and read other developer schemas

## Roles

Four core roles with a clear inheritance hierarchy:

```
Loader (standalone)

Analyst < Developer < Automation
```

### Role Descriptions

| Role | Purpose |
|------|---------|
| **Loader** | Standalone role (no inheritance). Reads and writes to raw databases. Used by ingestion services (dlt, Fivetran, etc.) |
| **Analyst** | Read-only access to analytics marts layer. Starting point for business users |
| **Developer** | Inherits Analyst. Plus: read raw databases, read/write `analytics_dev`, read CI and production analytics |
| **Automation** | Inherits Developer. Plus: read/write `analytics` (CI and production), create schemas. Used by dbt CI/CD |

### Role Permissions Summary

| Role | Raw (prod) | Raw (dev) | Analytics (prod) | Analytics (dev) | Analytics (CI) |
|------|-----------|-----------|-------------------|-----------------|----------------|
| **Loader** | read/write | read/write | — | — | — |
| **Analyst** | — | — | read (marts only) | — | — |
| **Developer** | read | read | read | read/write + create schema | read |
| **Automation** | read | read | read/write + create schema | read | read/write + create schema |

### Growing the Analyst Role

As marts expand into domain-specific schemas, create additional analyst roles scoped to specific domains:

- `finance_analyst` → read access to `mrt_finance` only
- `marketing_analyst` → read access to `mrt_marketing` only

This keeps the base `analyst` role simple (full marts access) while allowing fine-grained control as the organisation scales.

### Service Users & Compute (Snowflake-Specific)

- Each role gets its own compute warehouse (e.g., `LOADER_WH`, `ANALYST_WH`, `DEVELOPER_WH`, `AUTOMATION_WH`)
- Service users (`loader`, `automation`) use **key-pair authentication**, not passwords
- Service users are created with `type = 'SERVICE'`

## Platform-Specific Patterns

### Snowflake

Snowflake supports the full separation model — separate databases, future grants, role hierarchy, and dedicated warehouses. See [`examples/snowflake_setup.sql`](examples/snowflake_setup.sql) for a complete reference script.

### Databricks

- Use Unity Catalog for catalog separation (`raw`, `analytics`, `analytics_dev`)
- Map the 4 roles to Databricks groups; nest groups for inheritance
- Use grants on catalogs and schemas rather than individual tables
- Service principals replace service users for loader and automation

See [`examples/databricks_setup.sql`](examples/databricks_setup.sql) for a complete reference script.

### BigQuery

- Dataset naming encodes both database and schema: `raw_hubspot`, `analytics_staging`, `analytics_dev_marts`
- For stronger isolation, move raw datasets to a separate GCP project with cross-project grants
- Map the 4 roles to Google Groups (human users) and service accounts (loader, automation)
- IAM bindings at the dataset level: `dataViewer` for read, `dataEditor` for read/write

See [`examples/bigquery_setup.sh`](examples/bigquery_setup.sh) for a complete reference script.

### Postgres

- No cross-database queries — all schemas live in a single database
- Schema naming encodes the layer: `raw_<source>`, `staging`, `intermediate`, `marts`
- Use `GRANT USAGE ON SCHEMA` and `GRANT SELECT ON ALL TABLES IN SCHEMA` patterns
- Role inheritance works via `GRANT role TO role`, same as the Snowflake hierarchy
- No future grants — use `ALTER DEFAULT PRIVILEGES` to approximate them

See [`examples/postgres_setup.sql`](examples/postgres_setup.sql) for a complete reference script.

### DuckDB

- Single-user embedded database — no built-in roles, grants, or user management
- Security boundary is the file system: control who can access the `.duckdb` file(s)
- Use schemas for layer separation (`raw_<source>`, `staging`, `intermediate`, `marts`)
- For physical database separation, use `ATTACH` to connect separate `.duckdb` files

See [`examples/duckdb_setup.sql`](examples/duckdb_setup.sql) for a complete reference script.

## dbt Integration

dbt enforces part of the security model at build time through grants, custom database/schema resolution, and on-run-end hooks. This closes the gap between warehouse-level setup scripts and the actual permissions analysts and developers experience.

### Model-Level Grants (`+grants`)

Use the `+grants` config in `dbt_project.yml` to declare which roles can read which layers. dbt applies these grants when it builds the models.

```yaml
models:
  my_project:
    staging:
      +schema: staging

    intermediate:
      +schema: intermediate

    marts:
      +schema: marts
      +grants:
        select: ["analyst"]
```

Only the marts layer gets `+grants: select: ["analyst"]` — staging and intermediate are not granted to analysts, enforcing the principle that analysts only see consumer-facing models.

As domain-specific mart schemas emerge, scope grants to specific analyst roles:

```yaml
    marts:
      finance:
        +schema: mrt_finance
        +grants:
          select: ["analyst", "finance_analyst"]
      marketing:
        +schema: mrt_marketing
        +grants:
          select: ["analyst", "marketing_analyst"]
```

### Schema Usage Grants (`on-run-end` Hook)

dbt's built-in `+grants` only grants `SELECT` on individual objects (tables/views) — it does not grant `USAGE` on the schema itself. Without `USAGE`, roles cannot see the schema or its objects even if `SELECT` is granted.

The `grant_usage_on_schemas_where_select` macro runs as an `on-run-end` hook to automatically grant `USAGE` on every schema that contains models with `+grants: select`. It only runs in production (`'prod' in target.name`).

```yaml
on-run-end:
  - "{{ grant_usage_on_schemas_where_select() }}"
```

The macro iterates the dbt graph, collects all schemas where any model has a `select` grant, and issues the appropriate platform-specific grant statements. See [`examples/grant_usage_on_schemas.sql`](examples/grant_usage_on_schemas.sql) for the full implementation with Snowflake (default), Postgres, and Databricks (Spark) dispatches.

### Custom Database, Schema, and Alias Resolution

dbt uses three `generate_*` macros to determine the fully qualified name (`database.schema.alias`) of every model. Overriding these macros is how the security model's database separation and environment strategy are enforced at build time.

Each macro must exist in your dbt project's `macros/` directory. dbt calls them automatically — you do not invoke them directly. See the official docs for full context:
- [Custom databases](https://docs.getdbt.com/docs/build/custom-databases)
- [Custom schemas](https://docs.getdbt.com/docs/build/custom-schemas)
- [Custom aliases](https://docs.getdbt.com/docs/build/custom-aliases)

#### `generate_database_name` — Cross-database writes

**Why:** When raw and analytics live in separate databases, dbt needs to resolve databases other than `target.database`. The default implementation already supports this — if a model or source specifies a `database` config, the macro returns it; otherwise it falls back to `target.database`.

**Default behaviour (no override needed):** dbt's built-in implementation uses the `database` config if supplied, otherwise `target.database`. This is sufficient for the database separation strategy — sources reference `raw` while `target.database` points to `analytics`.

If you need to customise the logic (e.g., environment-specific database name mapping), override it at `macros/get_custom_database.sql`. See [`examples/get_custom_database.sql`](examples/get_custom_database.sql) for the default implementation.

#### `generate_schema_name` — Environment-aware schemas

**Why:** In production, models should write to bare schema names (`staging`, `intermediate`, `marts`). In development, they should be prefixed with the developer's target schema (`dbt_jsmith_staging`) to avoid collisions. dbt's default concatenates `target.schema` with `custom_schema_name` in **all** environments, which is not what we want.

**Override with `generate_schema_name_for_env`:** dbt provides a built-in alternative that handles the environment split:
- **Production** (`target.name = 'prod'`): uses `custom_schema_name` directly → `staging`, `intermediate`, `marts`
- **Development / CI**: uses `target.schema ~ '_' ~ custom_schema_name` → `dbt_jsmith_staging`, `dbt_jsmith_marts`

This override must exist at `macros/get_custom_schema.sql`. See [`examples/get_custom_schema.sql`](examples/get_custom_schema.sql) for the implementation.

**Important:** Never remove the `target.schema` fallback from this macro — without it, developers running `dbt build` would write directly to shared schemas and overwrite each other's work.

#### `generate_alias_name` — Model aliases

**Why:** The alias determines the final table/view name within the schema. dbt's default uses the model filename (or a custom `alias` config if provided). For versioned models, it appends `_v<version>`.

**Default behaviour (no override needed):** dbt's built-in implementation is typically sufficient. Override at `macros/get_custom_alias.sql` only if you need project-specific naming conventions (e.g., adding prefixes). See [`examples/get_custom_alias.sql`](examples/get_custom_alias.sql) for the default implementation.

## Anti-Patterns

- **Single admin role for everything** — no separation of concerns, impossible to audit
- **Giving developers write access to production** — all production writes should go through automation
- **Sharing service account credentials** — each service gets its own user and key pair
- **No environment separation** — development writes hitting production data
- **Granting `SELECT *` on raw to analysts** — raw may contain PII/PHI; analysts should only see the marts layer
- **Using password auth for service accounts** — key-pair auth is more secure and supports rotation

## Related Skills

- **[analytics-architecture](../analytics-architecture/SKILL.md)** — Platform decisions that inform security setup
- **[dlt-pipelines](../dlt-pipelines/SKILL.md)** — Loader role and raw database permissions
- **[dbt-staging](../dbt-staging/SKILL.md)** — Staging layer references raw database, first transformed layer in analytics

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

# Configure dbt Security

Set up dbt grants, custom schema/database resolution, profiles, and on-run-end hooks to enforce the security model at build time.

## Step 1: Understand the Order of Operations

Setup scripts and dbt have distinct responsibilities:

| Responsibility | Handled by |
|---------------|-----------|
| Create databases/catalogs | Setup script |
| Create roles and role hierarchy | Setup script |
| Grant database-level access (USAGE, CREATE SCHEMA) | Setup script |
| Grant future table-level SELECT (where supported) | Setup script (Snowflake future grants, Postgres DEFAULT PRIVILEGES) |
| Create schemas (staging, marts, etc.) | dbt at runtime (via CREATE SCHEMA grant) |
| Grant SELECT on specific models | dbt `+grants` config |
| Grant USAGE on schemas | dbt `on-run-end` hook |

This means setup scripts never reference specific schemas like `staging` or `marts` — those don't exist yet. The scripts only operate at the database/catalog level.

## Step 2: Configure Model-Level Grants

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

## Step 3: Add Schema Usage Grant Hook

dbt's built-in `+grants` only grants `SELECT` on individual objects (tables/views) — it does not grant `USAGE` on the schema itself. Without `USAGE`, roles cannot see the schema or its objects even if `SELECT` is granted.

The `grant_usage_on_schemas_where_select` macro runs as an `on-run-end` hook to automatically grant `USAGE` on every schema that contains models with `+grants: select`. It only runs in production (`'prod' in target.name`).

```yaml
on-run-end:
  - "{{ grant_usage_on_schemas_where_select() }}"
```

The macro iterates the dbt graph, collects all schemas where any model has a `select` grant, and issues the appropriate platform-specific grant statements. See [`examples/grant_usage_on_schemas.sql`](../examples/grant_usage_on_schemas.sql) for the full implementation with Snowflake (default), Postgres, and Databricks (Spark) dispatches.

## Step 4: Configure Custom Schema/Database Resolution

dbt uses three `generate_*` macros to determine the fully qualified name (`database.schema.alias`) of every model. Each macro must exist in your dbt project's `macros/` directory.

### `generate_schema_name` — Environment-aware schemas

**Why:** In production, models should write to bare schema names (`staging`, `intermediate`, `marts`). In development, they should be prefixed with the developer's target schema (`dbt_jsmith_staging`).

**Override with `generate_schema_name_for_env`:** dbt provides a built-in alternative:
- **Production** (`target.name = 'prod'`): uses `custom_schema_name` directly → `staging`, `intermediate`, `marts`
- **Development / CI**: uses `target.schema ~ '_' ~ custom_schema_name` → `dbt_jsmith_staging`, `dbt_jsmith_marts`

This override must exist at `macros/get_custom_schema.sql`. See [`examples/get_custom_schema.sql`](../examples/get_custom_schema.sql).

**Important:** Never remove the `target.schema` fallback — without it, developers running `dbt build` would write directly to shared schemas.

### `generate_database_name` — Cross-database writes

**Default behaviour (no override needed):** dbt's built-in implementation uses the `database` config if supplied, otherwise `target.database`. This is sufficient for the database separation strategy — sources reference `raw` while `target.database` points to `analytics`.

If you need to customise, override at `macros/get_custom_database.sql`. See [`examples/get_custom_database.sql`](../examples/get_custom_database.sql).

### `generate_alias_name` — Model aliases

**Default behaviour (no override needed):** Override at `macros/get_custom_alias.sql` only if you need project-specific naming conventions. See [`examples/get_custom_alias.sql`](../examples/get_custom_alias.sql).

## Step 5: Configure dbt Profiles

dbt profiles tie the security model together. Each target sets `target.database`, `target.schema`, and `target.name`.

```yaml
my_project:
  target: dev
  outputs:

    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      role: DEVELOPER
      warehouse: DEVELOPER_WH
      database: ANALYTICS_DEV
      schema: dbt_jsmith          # target.schema → developer namespace

    ci:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: AUTOMATION
      role: AUTOMATION
      warehouse: AUTOMATION_WH
      database: ANALYTICS_CI
      schema: dbt_ci              # target.schema → CI namespace

    prod:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: AUTOMATION
      role: AUTOMATION
      warehouse: AUTOMATION_WH
      database: ANALYTICS
      schema: dbt_prod            # target.schema → ignored in prod by generate_schema_name_for_env
```

| Field | Dev | CI | Prod |
|-------|-----|-----|------|
| `target.name` | `dev` | `ci` | `prod` |
| `target.database` | `ANALYTICS_DEV` | `ANALYTICS_CI` | `ANALYTICS` |
| `target.schema` | `dbt_jsmith` | `dbt_ci` | `dbt_prod` (unused) |
| **Role** | `DEVELOPER` | `AUTOMATION` | `AUTOMATION` |
| **Schema output** | `dbt_jsmith_staging` | `dbt_ci_staging` | `staging` |
| **Sources read from** | `RAW` (or `RAW_DEV` override) | `RAW` | `RAW` |

Sources default to reading from `raw` (prod). During pipeline development, override per source with a dbt var:

```yaml
# dbt_project.yml (or via CLI --vars)
vars:
  hubspot_database: RAW_DEV   # only while developing the hubspot pipeline
```

```yaml
# models/staging/hubspot/_hubspot__sources.yml
sources:
  - name: hubspot
    database: "{{ var('hubspot_database', 'RAW') }}"
```

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

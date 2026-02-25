# dbt Style & Structure

## Overview

This reference defines the foundational conventions for all dbt work. It covers project structure, naming, SQL style, Jinja style, and YAML style. Rather than duplicating dbt's official guidance, this reference **references the authoritative sources** and layers on opinionated defaults for consistency.

## Authoritative References

These are the official dbt best practice guides. **Read and follow these** — they are the source of truth:

| Topic | URL |
|-------|-----|
| Best practices hub | https://docs.getdbt.com/best-practices |
| How we structure dbt projects | https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview |
| How we style dbt projects | https://docs.getdbt.com/best-practices/how-we-style/0-how-we-style-our-dbt-projects |
| SQL style guide | https://docs.getdbt.com/best-practices/how-we-style/2-how-we-style-our-sql |
| Jinja style guide | https://docs.getdbt.com/best-practices/how-we-style/4-how-we-style-our-jinja |
| YAML style guide | https://docs.getdbt.com/best-practices/how-we-style/5-how-we-style-our-yaml |
| Materialization best practices | https://docs.getdbt.com/best-practices/materializations/1-guide-overview |

If the dbt MCP server is available, use its Discovery tools (`get_model_details`, `get_lineage`, `get_all_models`) to understand the existing project before making changes.

## Project Structure

dbt's structure guide defines three primary layers. Data flows from **source-conformed** (shaped by external systems) to **business-conformed** (shaped by business needs).

Reference: https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview

### Folder Layout

```
models/
├── staging/                 # 1:1 with source tables, organized by source system
│   ├── <source_name>/
│   │   ├── _<source_name>__sources.yml
│   │   ├── _<source_name>__models.yml
│   │   ├── stg_<source_name>__<entity>.sql
│   │   └── stg_<source_name>__<entity>.yml
│   └── ...
├── intermediate/            # Purpose-built transforms, organized by business concern
│   ├── <business_area>/
│   │   └── int_<entity>s_<verb>ed.sql
│   └── ...
└── marts/                   # Business-facing models, organized by department
    ├── <department>/
    │   ├── _<department>__models.yml
    │   └── <entity>.sql
    └── ...
```

### Layer Summary

| Layer | Naming | Organized By | Materialization | Exposed to Users |
|-------|--------|-------------|-----------------|-----------------|
| **Staging** | `stg_<source>__<entity>` | Source system | `view` | No |
| **Intermediate** | `int_<entity>s_<verb>ed` | Business concern | `ephemeral` | No |
| **Marts** | `fct_<entity>` / `dim_<entity>` | Department | `table` / `incremental` | Yes |

Reference: https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview

### Materialization Strategy

Configure at the directory level in `dbt_project.yml`:

```yaml
models:
  staging:
    +materialized: view
  intermediate:
    +materialized: ephemeral
  marts:
    +materialized: table
    finance:
      +schema: finance
    marketing:
      +schema: marketing
```

Reference: https://docs.getdbt.com/best-practices/materializations/1-guide-overview

## Naming Conventions

Reference: https://docs.getdbt.com/best-practices/how-we-style/1-how-we-style-our-dbt-models

### Models

- Use `snake_case` for all schema, table, and column names
- Pluralize model names: `customers`, `orders`, `payments`
- Use the double-underscore convention to separate source from entity: `stg_stripe__payments`
- Drop the double underscore at business-conformed layers (intermediate and marts)
- Do not abbreviate: `customers` not `cust`, `transactions` not `txn`
- Do not use reserved words as column names

### Columns

- **Primary keys**: `<object>_id` (e.g., `account_id`), string data type
- **Booleans**: prefix with `is_` or `has_` (e.g., `is_active`, `has_subscription`)
- **Timestamps**: `<event>_at` in UTC (e.g., `created_at`, `updated_at`, `deleted_at`)
- **Dates**: `<event>_date` (e.g., `created_date`)
- **Currency**: decimal format (19.99); suffix for alternates (`price_in_cents`)
- Use past tense for event descriptors: `created`, `updated`, `deleted`
- Convert camelCase source fields to snake_case

### Files

- YAML config per folder: `_<directory>__models.yml`, `_<directory>__sources.yml`
- Leading underscore sorts YAML to top of each folder
- One `.yml` file per `.sql` model (or one per folder for small projects)
- Docs blocks: `_<directory>__docs.md`

## SQL Style

Reference: https://docs.getdbt.com/best-practices/how-we-style/2-how-we-style-our-sql

### Formatting

- **4-space indentation** (no tabs)
- **Lowercase** for SQL keywords, field names, and function names
- Trailing commas
- Use explicit `as` keyword for all aliases
- Prefix column names with the model/CTE name when joining multiple tables

### CTEs

CTEs are the primary pattern for organizing dbt SQL. Every model should use CTEs rather than subqueries.

```sql
with

source as (
    select * from {{ source('stripe', 'payments') }}
),

renamed as (
    select
        id as payment_id,
        amount / 100.0 as amount,
        created::timestamp_ltz as created_at
    from source
)

select * from renamed
```

**Import CTEs** go at the top — one per `{{ ref() }}` or `{{ source() }}`:

```sql
with

orders as (
    select * from {{ ref('stg_jaffle_shop__orders') }}
),

payments as (
    select * from {{ ref('stg_stripe__payments') }}
),

...
```

### Joins

- Always use explicit join types: `inner join`, `left join` (never bare `join`)
- Always move left to right: prefer `left join` over `right join`
- Avoid table aliases, especially initialisms — use the full CTE/model name
- Prefix all column references with the source name when joining

### Aggregation

- Execute aggregations as early as possible on the smallest dataset
- Place fields before aggregates and window functions in the select
- Prefer `group by 1, 2` over listing column names

### Column Selection

Prefer `dbt_utils.star()` over explicit column lists in intermediate and mart models. This reduces maintenance — adding a new attribute at the staging layer flows through automatically without touching every downstream model.

```sql
-- Preferred: dynamic column selection
select
    {{ dbt_utils.generate_surrogate_key(['product_id']) }} as product_key,
    {{ dbt_utils.star(from=ref('stg_shopify__products'), relation_alias='products', except=[]) }}
from products
```

Use the `except` parameter to explicitly exclude columns you do not want to expose:

```sql
{{ dbt_utils.star(from=ref('stg_crm__customers'), relation_alias='customers', except=['_dlt_load_id', '_dlt_id']) }}
```

When using `dbt_utils.star()`:

- Always pass `relation_alias` when the CTE name differs from the ref, or when joining multiple models
- Use `except` to drop internal/metadata columns that should not propagate downstream
- The YAML schema file is the column contract with downstream consumers — not the SQL `select` list
- For models with [dbt contracts](https://docs.getdbt.com/docs/collaborate/govern/model-contracts) enabled, the contract enforces the column list at build time regardless of `star()`

`dbt_utils.get_filtered_columns_in_relation` is the companion macro for when you need column names as a list (e.g., for `generate_surrogate_key` to build a `hash_diff`):

```sql
{%- set column_names = dbt_utils.get_filtered_columns_in_relation(from=ref('stg_shopify__products'), except=[]) %}
{{ dbt_utils.generate_surrogate_key(column_names) }} as hash_diff
```

### Cross-Database Macros

Use cross-database macros to keep models portable across warehouse platforms. Two sources are available:

**dbt native macros** ([reference](https://docs.getdbt.com/reference/dbt-jinja-functions/cross-database-macros)):

Use dbt's built-in type macros for casting, as these resolve to the correct data type per platform:

```sql
-- Preferred: explicit cast with type macro
cast(column_name as {{ dbt.type_string() }})
cast(column_name as {{ dbt.type_int() }})
cast(column_name as {{ dbt.type_timestamp() }})
cast(null as {{ dbt.type_numeric() }})
```

Prefer `cast(... as {{ type_macro }})` over `{{ dbt.cast() }}` — the `cast` function syntax is universal across platforms and more readable. The `type_*` macros handle the platform differences (e.g., `string` vs `varchar` vs `text`).

Other useful dbt native macros: `dbt.concat()`, `dbt.date_trunc()`, `dbt.datediff()`, `dbt.safe_cast()`, `dbt.bool_or()`.

**dbt_utils macros** ([reference](https://hub.getdbt.com/dbt-labs/dbt_utils/latest/)):

Use `dbt_utils` for common operations that vary across platforms:

| Macro | Use Instead Of |
|-------|---------------|
| `dbt_utils.safe_divide(numerator, denominator)` | `numerator / nullif(denominator, 0)` |
| `dbt_utils.generate_surrogate_key([...])` | Platform-specific hashing |
| `dbt_utils.star(from=ref(...))` | Explicit column lists |
| `dbt_utils.pivot(...)` | Manual `case when` pivoting |
| `dbt_utils.date_spine(...)` | Recursive CTEs for date generation |

When in doubt, check if a dbt or dbt_utils macro exists before writing platform-specific SQL.

### Other SQL Conventions

- Prefer `union all` over `union` unless deduplication is required
- Use Jinja comments (`{# #}`) for SQL that should not compile
- Use `coalesce` over `ifnull` or `nvl` for portability

## Jinja Style

Reference: https://docs.getdbt.com/best-practices/how-we-style/4-how-we-style-our-jinja

- Spaces inside delimiters: `{{ this }}` not `{{this}}`
- 4-space indentation inside Jinja blocks
- Newlines to separate distinct logical sections
- Do not over-optimize whitespace control (`{%-` / `-%}`); prioritize readability

```jinja
{% macro cents_to_dollars(column_name, decimal_places=2) %}
    round({{ column_name }} / 100.0, {{ decimal_places }})
{% endmacro %}
```

## YAML Style

Reference: https://docs.getdbt.com/best-practices/how-we-style/5-how-we-style-our-yaml

- **2-space indentation**
- List syntax for single items: `['other_user']`
- Separate complex dictionary items with blank lines for readability
- Use the dbt JSON schema with your IDE for validation

## YAML Configuration

### Source YAML

Every source system must have a corresponding source YAML with:
- Dynamic database/schema references using Jinja vars
- Description for the source and each table
- Primary key tests (`not_null`, `unique`) on each table

### Model YAML

Every model must have a corresponding YAML file with at minimum:
- Model description
- Column-level descriptions for key business columns (progressive enrichment)

## Linting & Formatting

- **SQLFluff** for SQL linting (dbt templater) — or use the style conventions above when SQLFluff is not configured
- **Prettier** for YAML formatting
- **Ruff/Black** for Python model formatting

## Anti-Patterns

- **Monolithic YAML**: Do not put all models/sources in a single `schema.yml`. Split by folder.
- **Abbreviations**: Do not abbreviate table or column names.
- **Subqueries**: Use CTEs instead of nested subqueries.
- **`select *` in non-staging models**: Use `dbt_utils.star()` instead of bare `select *` — it is explicit about the source relation and supports `except` for column exclusion. Bare `select *` hides where columns originate; `star()` makes it traceable.
- **Platform-specific SQL when a cross-database macro exists**: Use `dbt_utils.safe_divide()` not `nullif` patterns, `dbt.type_string()` not `varchar`, etc.
- **Right joins**: Rewrite as left joins for readability.
- **Bare `join`**: Always specify `inner join`, `left join`, etc.
- **Time dimensions in model names**: Use `orders` not `orders_per_day`. Use metrics for time-based aggregation.
- **Department-specific variants**: Do not create `finance_orders` and `marketing_orders`. Build one `orders` mart.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

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
├── staging/                          # 1:1 with source objects, organized by source system
│   └── <source>/
│       ├── _<source>__sources.yml
│       ├── base/                     # optional pre-staging cleanup
│       │   └── base_<source>__<entity>.sql
│       ├── stg_<source>__<entity>.sql
│       ├── stg_<source>__<entity>.yml
│       └── stg_<source>__<entity>__<child>.sql   # a nested array, e.g. stg_quickbooks__invoice__line
├── intermediate/                     # Purpose-built transforms, organized by source system
│   ├── <source>/
│   │   ├── <topic>/                  # optional, e.g. double_entry/
│   │   │   └── int_<source>__<description>.sql
│   │   └── int_<source>__<description>.sql
│   └── conformed/                    # cross-source models drop the source
│       └── int_<entity>_<description>.sql
└── marts/
    └── core/
        ├── dimensions/
        │   ├── <source>/
        │   │   ├── dim_<source>_<entity>.sql
        │   │   └── bridge/
        │   │       └── bdg_<source>_<entity>_<entity>.sql
        │   └── dim_<entity>.sql      # conformed across sources, e.g. dim_date
        ├── facts/
        │   └── <source>/
        │       ├── fct_<source>_<process>.sql
        │       └── rpt_<source>_<report>.sql     # financial statements and reports
        └── reports/                  # cross-source reports
```

### Layer Summary

| Layer | Naming | Organized By | Materialization | Exposed to Users |
|-------|--------|-------------|-----------------|-----------------|
| **Staging** | `stg_<source>__<entity>`, nested arrays `stg_<source>__<entity>__<child>` | Source system | `view` | No |
| **Intermediate** | `int_<source>__<description>`; cross-source `int_<entity>_<description>` in `conformed/` | Source system | `ephemeral` | No |
| **Marts** | `dim_<source>_<entity>` / `fct_<source>_<process>` / `rpt_<source>_<report>` / `bdg_…`; conformed dimensions `dim_<entity>` | Type, then source | `table` / `incremental` | Yes |

Examples: `stg_quickbooks__invoice`, `stg_quickbooks__invoice__line`, `int_quickbooks__invoice_double_entry`, `int_quickbooks__account_classifications`, `dim_quickbooks_account`, `fct_quickbooks_general_ledger`, `rpt_quickbooks_balance_sheet`, `dim_date`.

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
- Name models in the **singular**, after the source object one row represents: `stg_quickbooks__invoice`, `dim_quickbooks_account`
- A double underscore separates the source from the rest in staging and intermediate: `stg_quickbooks__invoice`, `int_quickbooks__invoice_double_entry`. A nested array adds a second one: `stg_quickbooks__invoice__line`
- Marts use a single underscore after the prefix and source: `dim_quickbooks_account`, `fct_quickbooks_general_ledger`, `rpt_quickbooks_profit_and_loss`
- Models that combine sources drop the source: `int_job_conformed`, `dim_date`
- A model ported from a package (for example Fivetran's `dbt_quickbooks`) keeps the package's name and column names
- Don't invent abbreviations, but keep a source's own (`txn` in `LinkedTxn`) rather than respelling them
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

- Sources: `_<source>__sources.yml` in the staging folder; the leading underscore sorts it to the top
- One `.yml` file per `.sql` model, with the model's name: `stg_quickbooks__invoice.yml`
- Unit tests: `<model>_unit_tests.yml` next to the model
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
- **Invented abbreviations**: Don't shorten names yourself (`cust`, `amt`). A source's or a ported package's own names stay as they are.
- **Subqueries**: Use CTEs instead of nested subqueries.
- **`select *` in non-staging models**: Use `dbt_utils.star()` instead of bare `select *` — it is explicit about the source relation and supports `except` for column exclusion. Bare `select *` hides where columns originate; `star()` makes it traceable.
- **Platform-specific SQL when a cross-database macro exists**: Use `dbt_utils.safe_divide()` not `nullif` patterns, `dbt.type_string()` not `varchar`, etc.
- **Right joins**: Rewrite as left joins for readability.
- **Bare `join`**: Always specify `inner join`, `left join`, etc.
- **Time dimensions in model names**: Use `orders` not `orders_per_day`. Use metrics for time-based aggregation. A periodic snapshot with its own grain is a different model and is named for it: `fct_quickbooks_general_ledger_by_period`.
- **Department-specific variants**: Do not create `finance_orders` and `marketing_orders`. Build one `orders` mart.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

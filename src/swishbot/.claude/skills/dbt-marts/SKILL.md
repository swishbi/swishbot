---
name: dbt-marts
description: "Build the mart/gold layer in dbt. Use when creating final business-facing models — fact tables, dimension tables, wide denormalized tables, or aggregated metrics. The last transformation before consumption by BI tools or the semantic layer."
---

# dbt Mart Layer

## Overview

The mart layer is the final transformation layer in dbt. Mart models are the wide, rich, business-facing entities that end users, BI tools, and the semantic layer consume. They are organized by business department and use plain entity names.

Reference: https://docs.getdbt.com/best-practices/how-we-structure/4-marts

## When to Build a Mart

Create a mart model when:

- You need a **business entity** that end users will query (customers, orders, invoices)
- A BI tool or semantic layer needs a **stable, wide table** to build metrics on
- You are combining staging and/or intermediate models into a **denormalized, entity-grained** output

Do NOT build separate marts for:

- Different time granularities (`orders_per_day`) — use metrics/semantic layer instead
- Different departments wanting the same entity (`finance_orders`, `marketing_orders`) — build one `orders` mart

## Methodology

### Folder Organization

Organize by **department** or business area. Each department gets its own schema in the warehouse.

```
models/marts/
├── finance/
│   ├── _finance__models.yml
│   ├── orders.sql
│   └── payments.sql
├── marketing/
│   ├── _marketing__models.yml
│   └── customers.sql
└── operations/
    ├── _operations__models.yml
    └── work_orders.sql
```

Reference: https://docs.getdbt.com/best-practices/how-we-structure/4-marts

### Naming Convention

Use **plain entity names** — no prefix, no layer indicator. These are the business concepts:

- `customers` (not `mart_customers` or `fct_customers`)
- `orders`
- `invoices`
- `work_orders`

Avoid subfolders within a department until you have 10+ marts in that department.

### Materialization

Build marts as **tables** or **incremental** models. Never views — marts are the performance-optimized layer.

Progression path:
1. Start with `table`
2. Move to `incremental` when build times become excessive

```yaml
# dbt_project.yml
models:
  marts:
    +materialized: table
    finance:
      +schema: finance
    marketing:
      +schema: marketing
```

### Data Architecture

- **Wide and denormalized** — storage is cheap, compute is expensive. Include all relevant data.
- **Entity-grained** — each row represents one discrete instance of a concept (one customer, one order)
- **Include related data** — bring in dimensions from other entities rather than forcing users to join

### Complexity Management

- If a mart requires **4-5+ joins**, add intermediate models to break up the complexity
- Two intermediate models (3 concepts each) + one mart is more readable than 6 joins in one mart
- Cross-mart dependencies are allowed but should be deliberate and documented

## Patterns

### Pattern 1: Simple Mart (Direct from Staging)

```sql
with

orders as (
    select * from {{ ref('stg_jaffle_shop__orders') }}
),

payments as (
    select * from {{ ref('int_payments_pivoted_to_orders') }}
),

final as (
    select
        orders.order_id,
        orders.customer_id,
        orders.order_date,
        orders.status,
        payments.credit_card_amount,
        payments.bank_transfer_amount,
        payments.total_amount
    from orders
    left join payments
        on orders.order_id = payments.order_id
)

select * from final
```

### Pattern 2: Wide Denormalized Entity

```sql
with

customers as (
    select * from {{ ref('stg_jaffle_shop__customers') }}
),

orders as (
    select * from {{ ref('orders') }}
),

customer_orders as (
    select
        customer_id,
        min(order_date) as first_order_date,
        max(order_date) as most_recent_order_date,
        count(*) as order_count,
        sum(total_amount) as lifetime_value
    from orders
    group by 1
),

final as (
    select
        customers.customer_id,
        customers.first_name,
        customers.last_name,
        customer_orders.first_order_date,
        customer_orders.most_recent_order_date,
        customer_orders.order_count,
        coalesce(customer_orders.lifetime_value, 0) as lifetime_value
    from customers
    left join customer_orders
        on customers.customer_id = customer_orders.customer_id
)

select * from final
```

### Pattern 3: Incremental Mart

```sql
{{
    config(
        materialized='incremental',
        unique_key='event_id',
        incremental_strategy='merge'
    )
}}

with

events as (
    select * from {{ ref('stg_app__events') }}
    {% if is_incremental() %}
    where created_at > (select max(created_at) from {{ this }})
    {% endif %}
),

final as (
    select
        event_id,
        user_id,
        event_type,
        event_properties,
        created_at
    from events
)

select * from final
```

## Anti-Patterns

- **Department-specific variants** — Do not build `finance_orders` and `marketing_orders`. Build one `orders` mart and control access via schema permissions.
- **Time dimensions in model names** — Use `orders` not `orders_per_day`. Time aggregation belongs in the semantic layer or metrics.
- **Views for marts** — Marts should be tables or incremental. Views defeat the performance purpose.
- **Bare `select *`** — Use `dbt_utils.star()` instead of bare `select *`. It is explicit about the source relation and supports `except` for column exclusion. The YAML schema file documents the contract with downstream consumers, not the SQL select list.
- **Over-joining** — If you have 6+ joins, add intermediate models. Marts should be readable at a glance.
- **Narrow marts** — Marts should be wide and denormalized. Do not force downstream users to join marts together.
- **Prefixed names** — Use `customers` not `dim_customers` or `fct_orders`. The folder structure provides the context.

## Related Skills

- **[requirements-discovery](../requirements-discovery/SKILL.md)** — Upstream discovery process that defines what marts need to be built
- **[dbt-style](../dbt-style/SKILL.md)** — Foundational naming, SQL style, and structure conventions
- **[dbt-intermediate](../dbt-intermediate/SKILL.md)** — The upstream layer feeding into marts
- **[dbt-staging](../dbt-staging/SKILL.md)** — The first transformation layer
- **[dbt-mcp](../dbt-mcp/SKILL.md)** — Use `get_lineage` to understand downstream dependencies before modifying marts
- **[dimensional-modeling](../dimensional-modeling/SKILL.md)** — Design-level decisions for fact tables, dimension tables, grain, and conformance

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

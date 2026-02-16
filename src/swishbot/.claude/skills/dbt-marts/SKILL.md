---
name: dbt-marts
description: "Build the mart/gold layer in dbt. Use when a user asks to create a fact table, dimension table, wide denormalized model, aggregated metrics, or convert a mart to incremental. The last transformation before BI tools or the semantic layer."
argument-hint: "[model-name]"
---

# dbt Mart Layer

## Overview

The mart layer is the final transformation layer in dbt. Mart models are the wide, rich, business-facing entities that end users, BI tools, and the semantic layer consume. They are organized by business department and use plain entity names.

Reference: https://docs.getdbt.com/best-practices/how-we-structure/4-marts

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Create Mart Model](workflows/create-mart-model.md) | Building a new mart — confirm need, folder, naming, materialization, patterns |
| [Create Incremental Mart](workflows/create-incremental-mart.md) | Converting a table mart to incremental for performance |

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

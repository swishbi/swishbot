---
name: dbt-intermediate
description: "Build the intermediate/silver layer in dbt. Use when a user asks to join staged models, apply business logic between staging and marts, create cross-source integrations, or refactor complex mart logic into intermediate models."
argument-hint: "[model-name]"
---

# dbt Intermediate Layer

## Overview

The intermediate layer sits between staging and marts. It contains purpose-built transformation steps that prepare staging models for joining into wide, rich mart models. Intermediate models are the workbench — they isolate complex logic, simplify debugging, and keep mart models readable.

Reference: https://docs.getdbt.com/best-practices/how-we-structure/3-intermediate

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Create Intermediate Model](workflows/create-intermediate-model.md) | Building a new intermediate model — confirm need, name, materialize, write |
| [Refactor to Intermediate](workflows/refactor-to-intermediate.md) | Extracting complex logic from an existing mart into intermediate |

## Anti-Patterns

- **Exposing to end users** — Intermediate models are internal. If users need it, promote it to a mart.
- **1:1 with staging** — If you are just renaming columns or adding a filter to a single staging model, that logic belongs in staging or the mart.
- **Multiple downstream dependents** — If many marts reference the same intermediate model, consider whether it should be a mart itself.
- **Skipping the layer** — Do not join 6+ staging models directly in a mart. Add intermediate steps.
- **Source-system folder organization** — Organize by business concern. At this layer, the data's origin matters less than its purpose.

## Related Skills

- **[dbt-style](../dbt-style/SKILL.md)** — Foundational naming, SQL style, and structure conventions
- **[dbt-staging](../dbt-staging/SKILL.md)** — The upstream layer feeding into intermediate models
- **[dbt-marts](../dbt-marts/SKILL.md)** — The downstream layer consuming intermediate models
- **[dbt-mcp](../dbt-mcp/SKILL.md)** — Use `get_lineage` and `get_model_details` to understand the DAG before adding intermediate models
- **[dimensional-modeling](../dimensional-modeling/SKILL.md)** — Design-level decisions that drive what intermediate models are needed (cross-references, grain changes)

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

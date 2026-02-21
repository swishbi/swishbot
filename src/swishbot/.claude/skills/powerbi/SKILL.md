---
name: powerbi
description: "Apply Power BI best practices. Use when a user asks to build a report, design a Power BI semantic model, write DAX measures, set up deployment pipelines, configure workspaces, connect Excel to a dataset, parameterize M queries, or plan a Power BI rollout."
---

# Power BI

## Overview

This skill encodes an opinionated Power BI methodology built around eight core tenets. It assumes data arrives as star schemas from the warehouse (via **dbt-marts** and **dimensional-modeling**) and focuses on how to model, report, deploy, and consume that data inside the Power BI ecosystem.

Authoritative references:

- [Power BI implementation planning](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-implementation-planning-introduction)
- [Power BI guidance documentation](https://learn.microsoft.com/en-us/power-bi/guidance/)
- [Departmental BI scenario](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-implementation-planning-usage-scenario-departmental-bi)

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Design Semantic Model](workflows/design-semantic-model.md) | Planning which tables to import, model boundaries, single vs. split model decisions |
| [Build Semantic Model](workflows/build-semantic-model.md) | Creating or editing the model — M queries, relationships, DAX measures, naming conventions |
| [Build Report](workflows/build-report.md) | Building reports against a live-connected semantic model — layout, visuals, filters, audiences |
| [Deploy and Publish](workflows/deploy-and-publish.md) | Setting up workspaces, deployment pipelines (DEV/TEST/PROD), apps, refresh schedules |
| [Connect and Consume](workflows/connect-and-consume.md) | Connecting to the semantic model from Excel or external tools instead of exporting data |

## Core Tenets

### 1. Separate Semantic Models from Reports

Never build reports inside the same `.pbix` file that contains the data model. Publish the semantic model as a standalone dataset, then build reports that live-connect to it. This enables multiple reports to share one governed model and prevents model drift.

### 2. One Company-Wide Semantic Model

Default to a single semantic model that serves the entire organization. Split into separate models only when forced by row-level security boundaries that cannot be expressed in a single model, or when dataset size exceeds Premium capacity limits. Every split is a conformance risk — resist it.

### 3. One App, Multiple Audiences

Create a single Power BI app per workspace and use up to 10 audience groups to control what each team sees. Do not proliferate apps — audiences are the access-control mechanism.

### 4. Deployment Pipelines (DEV / TEST / PROD)

Use Power BI deployment pipelines with three workspaces: DEV, TEST, and PROD. Requires Premium Per User (PPU) or Premium capacity. All development happens in DEV; promotion to TEST and PROD is via the pipeline — never publish directly to PROD.

### 5. Star Schemas Only

The semantic model imports `dim_*` and `fct_*` tables directly from the warehouse mart layer. Do not reshape data inside Power BI — the warehouse owns the transformation logic. If something needs to change, change it in dbt.

### 6. Don't Export — Connect

Users should never export data from Power BI to CSV/Excel for further analysis. Instead, connect Excel pivot tables to the published semantic model via a live connection. This preserves governance, keeps a single source of truth, and lets users work in their familiar tool.

### 7. Parameterized M Queries

Every M query that references a database or schema must use Power Query parameters (`DbServer`, `DbName`, `DbSchema`) so the connection can be switched across environments (DEV/TEST/PROD) without editing queries. Deployment pipelines swap parameter values automatically during promotion.

### 8. Consistent DAX Naming Conventions

DAX measure and column names must be specific and unambiguous. Avoid short or generic names like `Amount` or `Count`. Prefer descriptive names like `Total Revenue (Excl Tax)` or `Active Customer Count (30d)`. Group related measures in display folders. Use TMDL format for version-controlled definitions.

## Examples

See [examples/](examples/) for reference files:
- `semantic_model.tmdl` — Complete semantic model in TMDL format showing all framework tables, field parameters, calculation groups, and parameterized M queries

## Anti-Patterns

- **Model inside the report .pbix** — Couples the dataset to a single report. Every new report duplicates the model, causing refresh sprawl and governance drift.
- **Multiple semantic models for the same data** — Creates conflicting metric definitions. One model, one truth.
- **Publishing directly to PROD** — Bypasses testing. Always promote through the deployment pipeline.
- **Reshaping data in Power Query** — If you need a new column or join, add it in dbt. Power BI should import clean star schemas, not rebuild them.
- **Exporting to CSV/Excel** — Breaks the single source of truth. Connect instead of exporting.
- **Hardcoded server/database in M queries** — Breaks environment promotion. Always parameterize.
- **Ambiguous DAX names** — `Revenue` could mean gross, net, or adjusted. Be explicit: `Total Revenue (Gross)`.
- **One app per team** — Creates fragmentation. Use one app with audience groups instead.

## Related Skills

- **[dimensional-modeling](../dimensional-modeling/SKILL.md)** — Star schema design decisions that determine what the semantic model imports
- **[dbt-marts](../dbt-marts/SKILL.md)** — The mart layer that produces the `dim_*` and `fct_*` tables consumed by the semantic model
- **[dbt](../dbt/SKILL.md)** — MetricFlow semantic models and metrics that BI tools can consume
- **[dagster](../dagster/SKILL.md)** — Orchestrate Power BI semantic model refreshes via Dagster

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

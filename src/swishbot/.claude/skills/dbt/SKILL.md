---
name: dbt
description: "Build the dbt transformation layer. Use for any dbt work — staging sources, building intermediate models, creating marts, defining MetricFlow semantic models and metrics, querying with mf CLI, applying SQL conventions, setting up dbt MCP, debugging errors, or reviewing project structure."
argument-hint: "[source-name-or-model-name]"
hooks:
  PreToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: prompt
          prompt: "Check if the file being written follows dbt naming conventions (stg_, int_, fct_, dim_ prefixes) and SQL style rules from references/style-and-conventions.md. If violations found, list them. $ARGUMENTS"
          timeout: 15
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: prompt
          prompt: "If the file just written is a staging model, verify it follows the CTE structure (source, renamed, final) defined in references/staging-sql-conventions.md. $ARGUMENTS"
          timeout: 15
---

# dbt Transformation Layer

## Overview

This skill covers the full dbt transformation stack — staging sources, building intermediate models, and delivering mart-layer tables. It routes every dbt task to a focused workflow or reference, and defines the behavioral rules that apply across all layers.

Official reference: https://docs.getdbt.com/best-practices

## Before Starting Any dbt Task

Follow these rules before writing or modifying any model:

**Look at the data first.** Use `dbt show` to preview source data or model output before writing SQL. Profile outputs — row counts, nulls, distributions — not just inputs. Never assume what the data looks like.

**Read existing YAML before touching a model.** When modifying an existing model, read its `description` and column descriptions first. They define the contract with downstream consumers.

**Check before creating.** Use `get_all_models` (Discovery API) or `dbt list` to verify the logic you need doesn't already exist in another model. Prefer extending over adding.

**DRY.** If two marts share a complex CTE, extract it to an intermediate model. If two staging models share a transformation pattern, that is a convention — document it in the YAML, not a new model.

## Cost Management

Managing warehouse compute costs is part of the job. Apply these practices during development:

| Practice | How |
|----------|-----|
| Preview before full run | `dbt show --select <model> --limit 50` during exploration |
| Reuse prod objects | `dbt run --defer --state path/to/prod/artifacts --select <model>` — builds only changed models |
| Zero-copy iteration | `dbt clone --select <model>` for large incremental tables |
| Always scope selects | `dbt build --select staging.source_name` — never run the full project without a selector |
| Limit test runs | `dbt test --select <model>` not `dbt test` |

## Routing Table

Find the right resource for your current task:

| Task | Resource |
|------|----------|
| New source system → stage it | [`workflows/staging/create-staging-source.md`](workflows/staging/create-staging-source.md) |
| Transform staging SQL (cast, rename, order) | [`workflows/staging/transform-staging-models.md`](workflows/staging/transform-staging-models.md) |
| Validate staging models with `dbt build` | [`workflows/staging/validate-staging-models.md`](workflows/staging/validate-staging-models.md) |
| Build a new intermediate model | [`workflows/intermediate/create-intermediate-model.md`](workflows/intermediate/create-intermediate-model.md) |
| Extract complex mart logic to intermediate | [`workflows/intermediate/refactor-to-intermediate.md`](workflows/intermediate/refactor-to-intermediate.md) |
| Build a mart model (fact, dim, wide) | [`workflows/marts/create-mart-model.md`](workflows/marts/create-mart-model.md) |
| Convert a mart to incremental | [`workflows/marts/create-incremental-mart.md`](workflows/marts/create-incremental-mart.md) |
| Define MetricFlow semantic model (entities, dimensions, measures) | [`workflows/semantic/define-semantic-model.md`](workflows/semantic/define-semantic-model.md) |
| Define and query MetricFlow metrics (simple, ratio, derived, cumulative) | [`workflows/semantic/define-semantic-model.md`](workflows/semantic/define-semantic-model.md) |
| SQL formatting, naming, folder structure | [`references/style-and-conventions.md`](references/style-and-conventions.md) |
| dbt MCP server setup and tool usage | [`references/mcp-setup-and-tools.md`](references/mcp-setup-and-tools.md) |
| Loader metadata (dlt, Fivetran, Airbyte) | [`references/loader-metadata.md`](references/loader-metadata.md) |
| Staging SQL conventions (CTE, casting, ordering) | [`references/staging-sql-conventions.md`](references/staging-sql-conventions.md) |

## Common Mistakes

| Anti-Pattern | Why It's Wrong | Fix |
|--------------|----------------|-----|
| Bare `select *` outside staging | Hides column origins, breaks contracts | Use `dbt_utils.star(from=ref(...))` with `except=[]` |
| Platform-specific SQL when a macro exists | Breaks portability | Use `dbt.type_string()`, `dbt_utils.safe_divide()`, etc. |
| Monolithic YAML | Unmaintainable; hard to review | One `.yml` file per `.sql` file (or per folder) |
| Abbreviations | Ambiguous; violates naming contracts | `customers` not `cust`, `transactions` not `txn` |
| Subqueries instead of CTEs | Hard to debug and test | Use CTEs everywhere |
| 6+ joins in one mart | Unreadable; hard to test | Add intermediate models at 4–5 joins |
| Views for mart materialization | Defeats the performance purpose | Use `table` or `incremental` for marts |
| Department-specific mart variants | Duplicates logic | Build one `orders` mart; control access via schema permissions |
| Time dimensions in model names | Confuses grain with aggregation | Use `orders` not `orders_per_day`; use metrics layer |
| Intermediate models exposed to users | Breaks the layer contract | If users need it, promote to a mart |
| Skipping the intermediate layer | Complex marts that are hard to debug | Create intermediate models for complex joins/aggregations |
| Organizing intermediate by source system | Wrong mental model at this layer | Organize by business concern, not source origin |

## Related Skills

- **[dimensional-modeling](../dimensional-modeling/SKILL.md)** — Design-level decisions (star schema, grain, SCD, bus matrix) that drive what models are needed
- **[dlt-pipelines](../dlt-pipelines/SKILL.md)** — Build dlt ingestion pipelines that feed into staging models
- **[dagster](../dagster/SKILL.md)** — Orchestrate dbt models as Dagster assets
- **[dba-security](../dba-security/SKILL.md)** — Database separation strategy and access control for warehouse objects

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

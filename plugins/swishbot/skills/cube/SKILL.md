---
name: cube
description: "Build and secure the Cube semantic layer on self-hosted Cube Core. Use when a user asks to model a dbt mart as a cube, define measures or dimensions, join a fact to its dimensions, create a view for Metabase or an AI agent, set up Cube's SQL API users, restrict who can query what, handle balances that must not sum over time, or check that Cube's numbers match the warehouse."
argument-hint: "[mart-or-view-name]"
---

# Cube Semantic Layer (Cube Core)

## Overview

Cube sits between the dbt marts and every consumer. dbt builds the tables; **Cube defines the metrics, once**. Metabase, AI agents and any other client query Cube, never the warehouse, so a measure means the same thing everywhere.

This skill covers **self-hosted Cube Core** (Docker, the `cubejs/cube` image) with a YAML data model. It doesn't cover Cube Cloud's dev-mode branches, deployments or `cube login`. For Cube Cloud, use Cube's official agent skills (`cube-js/cube-agent-skills`).

The layers:

| Object | What it is | Who sees it |
|--------|-----------|-------------|
| **Cube** | One per mart: table, primary key, dimensions, measures, joins | Nobody directly; deny-all access policy |
| **View** | The public contract: a named set of members from one or more cubes | Consumers, through an access policy |
| **Access policy** | Which group may query a view, and which rows | Enforced by Cube |
| **SQL API user** | A Postgres-protocol login mapped to a group | One per consumer (BI tool, agent) |

## Before Starting

**Read the existing model first.** Open the cubes, views and `cube.js` before changing anything. View and member names are a contract: dashboards and saved questions use them.

**Check the Cube version.** The `cubejs/cube` image tag decides the syntax. In Cube 1.x, views pull members in through `cubes:` with `join_path` and `includes` (the older view-level `measures:`/`dimensions:`/`joins:` keys are rejected), and access is enforced with access policies (`securityContext.canView` is gone).

**Look at the mart.** Know its grain and keys from the dbt model's YAML before you write a cube: one row per what?

**Never run dev mode against real data.** `CUBEJS_DEV_MODE` must be `false` in every shared environment; dev mode relaxes authentication.

## Workflows

| Task | Workflow |
|------|----------|
| Model a dbt mart as a cube (table, primary key, dimensions, refresh) | [`workflows/model-a-mart.md`](workflows/model-a-mart.md) |
| Define measures: sums, counts, ratios, signed totals, balances | [`workflows/define-measures.md`](workflows/define-measures.md) |
| Join a fact cube to its dimension cubes | [`workflows/join-dimensions.md`](workflows/join-dimensions.md) |
| Publish a view and decide who can query it (SQL API users, groups, access policies) | [`workflows/secure-with-views.md`](workflows/secure-with-views.md) |
| Prove Cube's numbers match the warehouse | [`workflows/test-the-model.md`](workflows/test-the-model.md) |

| Reference | Use for |
|-----------|---------|
| [`references/yaml-quick-reference.md`](references/yaml-quick-reference.md) | Keys for cubes, dimensions, measures, joins, views, access policies, pre-aggregations |
| [`references/cube-dbt.md`](references/cube-dbt.md) | Whether to generate cubes from dbt's manifest with `cube_dbt` |

| Example | Pattern |
|---------|---------|
| [`examples/rpt_quickbooks_profit_and_loss.yml`](examples/rpt_quickbooks_profit_and_loss.yml) | A fact cube: deny-all policy, data-dependent refresh key, signed measure, join |
| [`examples/dim_quickbooks_account.yml`](examples/dim_quickbooks_account.yml) | A dimension cube |
| [`examples/views.yml`](examples/views.yml) | A BI view and an aggregates-only agent view |
| [`examples/cube.js`](examples/cube.js) | SQL API users mapped to groups, failing closed |

## Principles

- **One cube per mart, named after the mart.** The cube's name never needs to change when consumers change.
- **Measures live in Cube only.** Consumers never re-aggregate raw columns. If a number is needed twice, it's a measure.
- **Views are the only door.** Every cube denies direct access; each consumer group gets views.
- **An agent's view has aggregates only.** No IDs, document numbers or names of people.
- **Balances are semi-additive.** A closing balance never sums across time periods.
- **Prove it against the warehouse.** A measure is done when its total equals the mart's total for the same filter.

## Anti-Patterns

- **Defining metrics in dbt.** dbt builds tables; metrics belong to Cube. No MetricFlow models alongside Cube.
- **Granting a cube directly.** A consumer that can query a cube sees every member, including IDs you meant to hide.
- **Renaming view members casually.** Every dashboard and saved question built on the view breaks. Alias in the view instead.
- **Summing a closing balance over months.** Twelve month-end balances added together mean nothing.
- **Joining without primary keys.** Cube needs a primary key on both sides to avoid fan-out.
- **A time-based refresh key on a file that changes on publish.** Cached results outlive the data they describe.
- **Shared SQL API credentials.** One login per consumer, so access policies can tell them apart.

## Related Skills

- **[dbt](../dbt/SKILL.md)** — Builds the marts that each cube reads
- **[dimensional-modeling](../dimensional-modeling/SKILL.md)** — Grain, facts and dimensions that cubes and joins mirror
- **[dba-security](../dba-security/SKILL.md)** — Least-privilege access; SQL API users follow the same principles
- **[powerbi](../powerbi/SKILL.md)** — The alternative semantic layer when the reporting tool is Power BI

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

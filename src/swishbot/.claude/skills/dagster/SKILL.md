---
name: dagster
description: "Orchestrate data pipelines with Dagster and Dagster+. Use when a user asks to set up a Dagster project, create assets, configure components, wire dlt or dbt into Dagster, define schedules, or debug orchestration issues."
argument-hint: "[component-type]"
---

# Dagster Orchestration

## Overview

Dagster is a data orchestrator for building, running, and observing data pipelines. We use **Dagster+ Serverless** (hosted) as our standard deployment target. Where possible, we use Dagster's **component system** (YAML-based declarative definitions) with custom components for project-specific needs.

References:
- Dagster docs: https://docs.dagster.io
- Components: https://docs.dagster.io/guides/build/components
- Dagster+ Serverless: https://docs.dagster.io/dagster-plus/deployment/serverless

## Project Structure

We use a **concept-based layout** with three top-level sibling directories rather than Dagster's default `src/` approach:

```
my-project/
├── ingestion/              # dlt pipelines (independently runnable)
│   ├── __init__.py
│   ├── destination.py      # Shared destination config
│   └── <source>/
│       └── <source>_pipeline.py
├── transformation/         # dbt project (independently runnable)
│   ├── dbt_project.yml
│   ├── models/
│   └── ...
├── orchestration/          # Dagster orchestration layer
│   ├── __init__.py
│   ├── definitions.py      # Single entry point
│   ├── defs/               # Component definitions (YAML + Python)
│   │   ├── ingestion/
│   │   │   └── dlt/
│   │   ├── transformation/
│   │   │   └── dbt/
│   │   └── reporting/
│   │       └── powerbi/
│   └── utils/              # Environment helpers, string utils
├── tests/
├── pyproject.toml
├── dagster_cloud.yaml
├── .env
└── Dockerfile
```

### Why This Layout

- **dlt and dbt are independently runnable** — they have their own CLIs and development workflows; burying them under `src/` makes direct use awkward
- **Dagster is the orchestrator, not the owner** — `orchestration/` references `ingestion/` and `transformation/` as siblings, which is the correct dependency direction
- **The component pattern still works** — `orchestration/defs/` uses YAML component definitions with custom Python components, exactly as Dagster intends

### When to Use Dagster's Default `src/` Layout

Use the standard `src/my_project/` approach when:
- The project has multiple independent code locations in a monorepo
- There are conflicting Python dependency requirements between locations
- The project has no external tools (no dbt, no dlt) — just pure Dagster assets

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Set Up Project](workflows/setup-project.md) | Starting a new Dagster project — directory structure, pyproject.toml, definitions.py, dagster_cloud.yaml |
| [Add dlt Component](workflows/add-dlt-component.md) | Wiring a dlt pipeline into Dagster as assets using DltLoadCollectionComponent |
| [Add dbt Component](workflows/add-dbt-component.md) | Wiring a dbt project into Dagster using DbtProjectComponent |
| [Add Custom Component](workflows/add-custom-component.md) | Extending base components with custom translators, automation conditions, or asset specs |

## Core Concepts

### Definitions Entry Point

Every Dagster project has a single `definitions.py` that Dagster loads on startup. We use `load_from_defs_folder()` to auto-discover all component definitions:

```python
from pathlib import Path
from dagster import definitions, load_from_defs_folder

@definitions
def defs():
    return load_from_defs_folder(project_root=Path(__file__).parent.parent)
```

### Component Definitions (YAML)

Each integration (dlt source, dbt project, Power BI workspace) is defined as a component in `defs/` with a `defs.yaml` file. Components are declarative — they wire sources to Dagster assets without imperative Python boilerplate.

### Custom Components (Python)

When the built-in component doesn't handle your use case (custom asset keys, automation conditions, partitioning), subclass the base component in a `component.py` file alongside the `defs.yaml`.

### Automation Conditions

We prefer **automation conditions** over traditional schedules/sensors for most assets:

| Pattern | When to Use |
|---------|-------------|
| `cron_tick_passed` + `~in_progress` | Source assets (ingestion) — run on schedule, skip if still running |
| `eager` | Downstream assets (transformation, reporting) — run immediately when dependencies complete |
| `on_cron` | Seeds, sources with no dependencies — fixed schedule |

### Environment Awareness

Use environment helpers to switch between local, branch, and production configs:

```python
def get_env() -> str:
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "prod":
        return "PROD"
    return "LOCAL"
```

## Anti-Patterns

- **Putting dbt/dlt inside the Dagster package** — they should be sibling directories, independently runnable
- **Defining resources inside component YAML** — resources belong in a shared `resources.py`, not scattered in each component
- **Skipping automation conditions** — use `cron_not_in_progress` for sources and `eager` for downstream rather than manual schedules
- **Hardcoding environment logic** — use a single `get_env()` helper and derive all env-specific config from it
- **Building all components at once** — wire one integration at a time, validate in the Dagster UI, then add the next

## Related Skills

- **[dlt](../dlt/SKILL.md)** — Build the dlt sources that Dagster orchestrates
- **[dbt](../dbt/SKILL.md)** — Build the dbt models that Dagster orchestrates
- **[powerbi](../powerbi/SKILL.md)** — Power BI semantic models that Dagster can refresh

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

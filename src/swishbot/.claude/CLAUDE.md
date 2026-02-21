# Project Guidelines

## Overview

This project uses [swishbot](https://github.com/swishbi/swishbot) skills to guide Claude through data engineering and analytics work. Skills are installed to `~/.claude/skills/` and encode opinionated methodology for each layer of the data stack.

## Quick Start

Start each session by invoking the agent for your work type. Agents load all relevant skills simultaneously and apply role-specific behavioral rules.

| Work Type | Agent | How to Invoke |
|-----------|-------|---------------|
| dbt models + dimensional schema design | `analytics-engineer` | "Act as the analytics-engineer agent" |
| Data pipelines (dlt/APIs) | `data-engineer` | "Act as the data-engineer agent" |
| Requirements / discovery / data validation | `business-analyst` | "Act as the business-analyst agent" |
| Infrastructure / security | `platform-engineer` | "Act as the platform-engineer agent" |

For ad-hoc tasks that don't fit an agent, reference the relevant skill directly: "Use the dbt skill to..."

## Installed Skills

<!-- Run `swishbot list` to see available skills. -->
<!-- Add the skills relevant to this project below. -->

### Discovery & Planning
| Skill | Description | Status |
|-------|-------------|--------|
| business-logic-mapping | Map tribal knowledge from SMEs into implementation-ready business logic tied to staging columns | :white_check_mark: |
| requirements-discovery | Act as a business analyst to guide stakeholders from idea to implementation-ready requirements | :white_check_mark: |

### Infrastructure
| Skill | Description | Status |
|-------|-------------|--------|
| dba-security | DBA security practices | :white_check_mark: |
| iac-terraform | Deploying infrastructure using Terraform/IaC | :x: |

### Ingestion
| Skill | Description | Status |
|-------|-------------|--------|
| dlt-pipelines | Writing dlt/Python ingestion pipelines | :white_check_mark: |

### Orchestration
| Skill | Description | Status |
|-------|-------------|--------|
| dagster | Orchestrate data pipelines with Dagster and Dagster+ | :white_check_mark: |

### Transformation (dbt)
| Skill | Description | Status |
|-------|-------------|--------|
| dbt | All dbt layers — staging, intermediate, marts, SQL conventions, MCP tooling | :white_check_mark: |
| dimensional-modeling | Dimensional modeling best practices | :white_check_mark: |

### Analytics & Presentation
| Skill | Description | Status |
|-------|-------------|--------|
| powerbi | Power BI best practices | :white_check_mark: |

## Installed Agents

<!-- Agents compose multiple skills into a focused persona. Install with: swishbot install --agent <agent-name> -->

| Agent | Description |
|-------|-------------|
| analytics-engineer | Designs dimensional schemas and builds dbt models across all layers with MCP tooling |
| business-analyst | Guides stakeholders from idea to implementation-ready spec; validates sources with dbt MCP |
| data-engineer | Builds ingestion pipelines with proper security |
| platform-engineer | Sets up infrastructure, security, and platform architecture |

## Security

See [SECURITY.md](SECURITY.md) for security guidelines covering SQL safety, credential handling, prompt injection defense, and pipeline safety. Skills with hooks enforce these rules automatically.

## Conventions

- Follow the methodology defined in each installed skill before applying general knowledge.
- Prefer platform-agnostic patterns unless the project targets a specific platform.
- Use `snake_case` for SQL objects and Python code.
- Every dbt source must have a corresponding YAML schema entry with at minimum a description and primary key test.
- Every dbt model must have a corresponding YAML file with at minimum a description.
- Write idempotent, incremental-friendly transformations where applicable.

## Stack Philosophy

This project follows a code-first approach using open-source technologies:

- **Ingestion:** dlt — Python pipelines, not GUI ETL tools
- **Transformation:** dbt — SQL models with version control, testing, and documentation
- **Orchestration:** Dagster+ Serverless — asset-based orchestration with automation conditions
- **Presentation:** Power BI — semantic models backed by warehouse star schemas

Everything is backed by code. No drag-and-drop, no GUI-configured pipelines, no manual deployments. Changes flow through version control with clean separation of dev/CI/prod environments.

## Project Structure

```
├── ingestion/              # dlt pipelines (independently runnable)
├── transformation/         # dbt project (independently runnable)
├── orchestration/          # Dagster orchestration layer
│   ├── definitions.py      # Single entry point
│   └── defs/               # Component definitions (YAML + Python)
│       ├── ingestion/dlt/  # dlt components
│       ├── transformation/ # dbt component
│       └── reporting/      # Power BI component
├── tests/
├── pyproject.toml
├── dagster_cloud.yaml
└── .claude/                # Skills, agents, memory
```

## Platform & Environment

<!-- Fill in for your project: -->
<!-- - Warehouse: Snowflake / BigQuery / Databricks / Postgres -->
<!-- - Python: 3.12+ -->

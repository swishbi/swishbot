# Project Guidelines

## Overview

This project uses [swishbot](https://github.com/swishbi/swishbot) skills to guide Claude through data engineering and analytics work. Skills are installed to `~/.claude/skills/` and encode opinionated methodology for each layer of the data stack.

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
| analytics-architecture | Analytics reference architecture | :x: |
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
| dbt-intermediate | Building the intermediate/silver layer | :white_check_mark: |
| dbt-marts | Building the mart/gold layer | :white_check_mark: |
| dbt-mcp | Configure and use the dbt MCP server with Claude | :white_check_mark: |
| dbt-staging | Building the staging/bronze layer | :white_check_mark: |
| dbt-staging-model | Conventions for writing a dbt staging model SQL file | :white_check_mark: |
| dbt-style | Cross-cutting dbt style, naming, and project structure conventions | :white_check_mark: |
| dimensional-modeling | Dimensional modeling best practices | :white_check_mark: |

### Analytics & Presentation
| Skill | Description | Status |
|-------|-------------|--------|
| powerbi | Power BI best practices | :white_check_mark: |
| semantic-layer | Building the semantic layer | :x: |

## Installed Agents

<!-- Agents compose multiple skills into a focused persona. Install with: swishbot install --agent <agent-name> -->

| Agent | Description |
|-------|-------------|
| analytics-engineer | Builds dbt models across all layers with MCP tooling |
| business-analyst | Guides stakeholders from idea to implementation-ready spec |
| data-engineer | Builds ingestion pipelines with proper security |
| data-modeler | Designs and builds dimensional models across the full dbt DAG |
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

## Project Structure

<!-- Describe your project layout here so Claude understands the codebase. -->
<!--
```
├── dbt/              # dbt project
├── pipelines/        # dlt ingestion pipelines
├── infra/            # Terraform infrastructure
├── dashboards/       # Power BI / reporting
└── ...
```
-->

## Platform & Environment

<!-- Uncomment and fill in the details for your stack: -->
<!--
- Warehouse: Snowflake / BigQuery / Databricks / Postgres
- Orchestrator: Dagster / Airflow / Prefect
- BI Tool: Power BI / Looker / Tableau
- Python: 3.12
-->

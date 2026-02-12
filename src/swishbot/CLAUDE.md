# Project Guidelines

## Overview

This project uses [swishbot](https://github.com/swishbi/swishbot) skills to guide Claude through data engineering and analytics work. Skills are installed to `~/.claude/skills/` and encode opinionated methodology for each layer of the data stack.

## Installed Skills

<!-- Run `swishbot list` to see available skills. -->
<!-- Add the skills relevant to this project below. -->

| Skill | Description | Status |
|-------|-------------|--------|
| dbt-staging | Building the staging/bronze layer | :x: |
| dbt-intermediate | Building the intermediate/silver layer | :x: |
| dbt-marts | Building the mart/gold layer | :x: |
| dlt-pipelines | Writing dlt/Python ingestion pipelines | :x: |
| iac-terraform | Deploying infrastructure using Terraform/IaC | :x: |
| dimensional-modeling | Dimensional modeling best practices | :x: |
| dba-security | DBA security practices | :x: |
| analytics-architecture | Analytics reference architecture | :x: |
| semantic-layer | Building the semantic layer | :x: |
| powerbi | Power BI best practices | :x: |

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

---
name: dbt-mcp
description: "Configure and use the dbt MCP server with Claude. Use when setting up the dbt MCP integration or when deciding which MCP tools to use for dbt development workflows."
---

# dbt MCP Server Integration

## Overview

The dbt MCP server bridges Claude with dbt infrastructure, exposing dbt Core, dbt Cloud, and dbt Fusion capabilities as MCP tools. It gives Claude the ability to run dbt commands, explore project metadata, query the semantic layer, and generate code — all within the conversation.

**This skill covers setup and tool usage patterns.** For methodology on *what* to build and *how* to structure it, see the layer-specific skills (`dbt-staging`, `dbt-intermediate`, `dbt-marts`) and `dbt-style`.

References:
- Repository: https://github.com/dbt-labs/dbt-mcp
- Official docs: https://docs.getdbt.com/docs/dbt-ai/about-mcp

## Setup

### Prerequisites

- **`uv`** installed: https://docs.astral.sh/uv/getting-started/installation/
- A local dbt project (for CLI tools)
- A dbt Cloud account (for Discovery, Semantic Layer, Admin API tools — optional)

### Claude Code (CLI)

**Local only (no dbt Cloud):**

```bash
claude mcp add dbt \
  -e DBT_PROJECT_DIR=/path/to/your/dbt/project \
  -e DBT_PATH=/path/to/your/dbt/executable \
  -- uvx dbt-mcp
```

**Local + dbt Cloud (OAuth):**

```bash
claude mcp add dbt \
  -e DBT_HOST=abc123.us1.dbt.com \
  -e DBT_PROJECT_DIR=/path/to/your/dbt/project \
  -e DBT_PATH=/path/to/your/dbt/executable \
  -- uvx dbt-mcp
```

**Using a .env file:**

```bash
claude mcp add dbt -- uvx --env-file /path/to/.env dbt-mcp
```

### Claude Desktop / Cursor (JSON)

```json
{
  "mcpServers": {
    "dbt": {
      "command": "uvx",
      "args": ["dbt-mcp"],
      "env": {
        "DBT_PROJECT_DIR": "/path/to/your/dbt/project",
        "DBT_PATH": "/path/to/your/dbt/executable"
      }
    }
  }
}
```

### Enable Optional Tool Groups

Some tool groups are disabled by default. Enable them with environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DISABLE_DBT_CLI` | `false` | dbt Core CLI commands (build, run, test, compile) |
| `DISABLE_DISCOVERY` | `false` | Discovery API (model details, lineage, sources) |
| `DISABLE_SEMANTIC_LAYER` | `false` | Semantic Layer (metrics, saved queries) |
| `DISABLE_ADMIN_API` | `false` | Admin API (jobs, runs) |
| `DISABLE_SQL` | `true` | Set to `false` to enable SQL execution and text-to-SQL |
| `DISABLE_DBT_CODEGEN` | `true` | Set to `false` to enable model/source YAML generation |
| `DISABLE_LSP` | `false` | dbt Fusion / LSP tools (column-level lineage) |

## Tool Categories

### CLI Tools (Local Only)

Run dbt commands directly. Use these during active development.

| Tool | Use When |
|------|----------|
| `build` | Running models, tests, snapshots, and seeds in DAG order |
| `run` | Materializing models in the database |
| `test` | Validating data and model integrity |
| `compile` | Checking Jinja logic without executing SQL |
| `show` | Previewing query results |
| `list` | Finding resources by type or selector |
| `parse` | Validating project syntax |
| `docs` | Generating documentation |

### Discovery Tools (dbt Cloud)

Explore project metadata without running anything. Use these to understand before you change.

| Tool | Use When |
|------|----------|
| `get_all_models` | Surveying the project |
| `get_model_details` | Understanding a specific model's columns, SQL, schema |
| `get_model_parents` / `get_model_children` | Tracing dependencies |
| `get_lineage` | Visualizing the DAG around a model |
| `get_model_health` | Checking run status, test results, source freshness |
| `get_all_sources` | Reviewing available sources |
| `get_source_details` | Inspecting source columns and freshness |
| `search` | Finding resources across the project |

### Codegen Tools (Local, Disabled by Default)

Generate boilerplate. Enable with `DISABLE_DBT_CODEGEN=false`.

| Tool | Use When |
|------|----------|
| `generate_source` | Creating source YAML from database introspection |
| `generate_model_yaml` | Generating model YAML with columns |
| `generate_staging_model` | Scaffolding staging SQL from a source table |

### Semantic Layer Tools (dbt Cloud)

Query metrics and saved queries. Use for analytics exploration.

| Tool | Use When |
|------|----------|
| `list_metrics` | Discovering available metrics |
| `query_metrics` | Running metric queries with filters and grouping |
| `get_dimensions` / `get_entities` | Understanding metric structure |

### Admin API Tools (Local + dbt Cloud)

Manage dbt Cloud jobs and runs.

| Tool | Use When |
|------|----------|
| `list_jobs` | Reviewing configured jobs |
| `trigger_job_run` | Kicking off a job |
| `get_job_run_details` | Checking run status |
| `get_job_run_error` | Debugging failures |

## Workflow Patterns

### Building a New Staging Source

1. Use `get_all_sources` to check if the source already exists
2. Use `generate_source` to scaffold source YAML from the database (if codegen enabled)
3. Use `generate_staging_model` to scaffold staging SQL (if codegen enabled)
4. Follow the `dbt-staging` skill methodology for the full workflow
5. Use `run` and `test` to validate

### Exploring an Existing Project

1. Use `get_all_models` to survey the project
2. Use `get_lineage` to understand the DAG around a specific area
3. Use `get_model_details` to inspect specific models
4. Use `get_model_health` to check for failing tests or stale sources

### Debugging a Failing Model

1. Use `get_model_health` to check the model's status
2. Use `compile` to inspect the generated SQL
3. Use `show` to preview results
4. Use `get_model_parents` to trace upstream dependencies
5. Use `test` with a selector to run specific tests

### Adding an Intermediate or Mart Model

1. Use `get_lineage` to understand what staging models are available
2. Use `get_model_details` on upstream models to understand their columns
3. Build the model following `dbt-intermediate` or `dbt-marts` skill methodology
4. Use `run` and `test` to validate
5. Use `get_model_children` to verify downstream impact

## Security Considerations

The dbt MCP server can modify data models, sources, and warehouse objects. Only enable it in trusted environments. Key precautions:

- The CLI tools (`run`, `build`) will execute against your connected warehouse
- `trigger_job_run` will start actual dbt Cloud jobs
- Review generated SQL with `compile` before running
- Use `show` to preview results before materializing

## Environment Variable Reference

### Core Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DBT_PROJECT_DIR` | Yes (CLI) | Path to folder containing `dbt_project.yml` |
| `DBT_PATH` | Yes (CLI) | Path to dbt executable |
| `DBT_HOST` | Yes (Cloud) | dbt platform hostname |
| `DBT_TOKEN` | Yes (non-OAuth) | Personal or service token |
| `DBT_PROD_ENV_ID` | Yes (Cloud) | Production environment ID |
| `DBT_DEV_ENV_ID` | Optional | Development environment ID |

### Debugging

| Variable | Default | Description |
|----------|---------|-------------|
| `DBT_MCP_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `DBT_MCP_SERVER_FILE_LOGGING` | `false` | Set to `true` to log to `./dbt-mcp.log` |
| `DBT_CLI_TIMEOUT` | `60` | Seconds before CLI command timeout |

## Related Skills

- **[dbt-style](../dbt-style/SKILL.md)** — Foundational conventions (the "what" and "how")
- **[dbt-staging](../dbt-staging/SKILL.md)** — Staging layer workflow
- **[dbt-intermediate](../dbt-intermediate/SKILL.md)** — Intermediate layer methodology
- **[dbt-marts](../dbt-marts/SKILL.md)** — Mart layer methodology
- **[dlt-pipelines](../dlt-pipelines/SKILL.md)** — Build dlt ingestion pipelines upstream of dbt

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

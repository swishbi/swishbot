---
name: dlt-pipelines
description: "Write dlt/Python data ingestion pipelines. Use when building extract-load pipelines from APIs, databases, files, or other sources into a data warehouse."
---

# dlt Pipelines

## Overview

dlt (data load tool) is a Python library for building extract-load pipelines. The open-source `dlt` library (`pip install dlt`) is all you need to build pipelines. dlt also offers **dltHub Workspace** (`pip install "dlt[workspace]"`) which adds an MCP server, an LLM-native init scaffold, and other tooling — some workspace features are free, others require a license. Check https://dlthub.com for current pricing.

This skill focuses on **setup and workflow patterns** rather than dlt internals.

References:
- dlt open-source: https://github.com/dlt-hub/dlt
- LLM-native workflow (workspace): https://dlthub.com/docs/dlt-ecosystem/llm-tooling/llm-native-workflow
- MCP server (workspace): https://dlthub.com/docs/hub/features/mcp-server

## dlt's Claude Code Reference

dlt maintains a detailed reference for building REST API pipelines with Claude Code, covering authentication methods, pagination strategies, incremental loading, data selection, and end-to-end examples. **Fetch this when building or debugging a dlt pipeline:**

https://raw.githubusercontent.com/dlt-hub/verified-sources/master/ai/claude/CLAUDE.md

## Initialise a Pipeline (Workspace)

Requires `dlt[workspace]`. Scaffolds a project with source-specific docs and a working template.

```bash
dlt init dlthub:<source> <destination>
```

Examples:
```bash
dlt init dlthub:github duckdb
dlt init dlthub:sql_database snowflake
dlt init dlthub:rest_api bigquery
```

This generates:
- A pipeline template file (e.g. `github_pipeline.py`)
- An LLM scaffold YAML with source-specific documentation
- `.dlt/` configuration and secrets files

### Working with the Scaffold

1. **Start with one endpoint** — get a single resource working end-to-end before adding more
2. **Delete what you don't understand** — if the scaffold includes unfamiliar patterns, remove them to keep Claude focused and reduce the surface for bugs
3. **Validate incrementally** — run the pipeline after each endpoint to catch issues early
4. **Reference the scaffold docs** — the generated YAML contains source-specific documentation; point Claude at it with `@` references when asking for help

## MCP Server (Workspace)

Requires `dlt[workspace]`. The dlt MCP server gives Claude direct access to pipeline metadata, loaded data, and documentation. It runs in two contexts:

### Workspace MCP (project-level)

Exposes workspace-wide tools for exploring pipelines, schemas, and documentation.

```bash
dlt workspace mcp
```

Default port: **43654**

### Pipeline MCP (pipeline-level)

Exposes tools scoped to a specific pipeline — schema exploration, destination table access, and SQL queries.

```bash
dlt pipeline <pipeline-name> mcp
```

Default port: **43656**

### Claude Code Configuration

Add the MCP servers to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "dlt-workspace": {
      "url": "http://127.0.0.1:43654/"
    },
    "dlt-pipeline": {
      "url": "http://127.0.0.1:43656/"
    }
  }
}
```

Both servers use SSE transport. You can run workspace and pipeline servers simultaneously.

### MCP Capabilities

| Capability | Use When |
|------------|----------|
| Explore pipeline schemas | Understanding what a pipeline loads and how it's structured |
| Access destination tables | Inspecting loaded data without leaving the conversation |
| Write SQL queries | Querying destination tables for validation or exploration |
| Debug pipeline traces | Investigating pipeline run failures *(in development)* |

## Workflow

### Building a New Pipeline

1. Run `dlt init dlthub:<source> <destination>` and select Claude Code
2. Start the MCP servers (`dlt workspace mcp` and/or `dlt pipeline <name> mcp`)
3. Focus on **one resource at a time** — get it loading correctly before moving on
4. Validate loaded data using the MCP server's table access tools
5. Add the next resource and repeat

### Debugging a Failing Pipeline

1. Use the pipeline MCP server to inspect the schema and loaded data
2. Check pipeline traces for error details
3. Simplify — isolate the failing resource and test it independently
4. Use `dlt pipeline <name> show` to inspect pipeline state

### Connecting to dbt

Once data is loaded, dbt picks up from the destination. Cross-reference:
- Use `dbt-staging` skill methodology to build staging models over dlt-loaded tables
- Use `dbt-mcp` to explore loaded schemas from the dbt side

## Anti-Patterns

- **Skipping the scaffold** — `dlt init` generates source-specific docs and a working template; starting from scratch means Claude lacks that context
- **Building all resources at once** — iterate one endpoint at a time; debugging multiple new resources simultaneously is slow and error-prone
- **Ignoring the MCP server** — querying loaded data through Claude is faster than switching to a SQL client for validation
- **Over-customising the scaffold** — the generated template is a starting point; keep it simple and let dlt handle schema inference and state management

## Related Skills

- **[dbt-staging](../dbt-staging/SKILL.md)** — Build staging models over dlt-loaded tables
- **[dbt-mcp](../dbt-mcp/SKILL.md)** — Explore loaded schemas from the dbt side
- **[analytics-architecture](../analytics-architecture/SKILL.md)** — Where dlt fits in the overall platform

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

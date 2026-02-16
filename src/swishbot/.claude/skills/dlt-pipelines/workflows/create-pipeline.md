# Create Pipeline

Build a new dlt extract-load pipeline from initialization through validation.

## Step 1: Initialize the Pipeline

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

## Step 2: Start MCP Servers

Requires `dlt[workspace]`. The dlt MCP server gives Claude direct access to pipeline metadata, loaded data, and documentation.

### Workspace MCP (project-level)

```bash
dlt workspace mcp
```

Default port: **43654**

### Pipeline MCP (pipeline-level)

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

## Step 3: Build Resources Iteratively

1. Focus on **one resource at a time** — get it loading correctly before moving on
2. Run the pipeline after each resource to catch issues early
3. Validate loaded data using the MCP server's table access tools
4. Add the next resource and repeat

### MCP Capabilities

| Capability | Use When |
|------------|----------|
| Explore pipeline schemas | Understanding what a pipeline loads and how it's structured |
| Access destination tables | Inspecting loaded data without leaving the conversation |
| Write SQL queries | Querying destination tables for validation or exploration |
| Debug pipeline traces | Investigating pipeline run failures *(in development)* |

## Step 4: Connect to dbt

Once data is loaded, dbt picks up from the destination. Cross-reference:
- Use `dbt-staging` skill methodology to build staging models over dlt-loaded tables
- Use `dbt-mcp` to explore loaded schemas from the dbt side

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

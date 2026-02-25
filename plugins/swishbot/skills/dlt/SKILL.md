---
name: dlt
description: "Write dlt/Python data ingestion pipelines. Use when a user asks to ingest data from an API, database, or file into a warehouse, create a new EL pipeline, debug a failing pipeline, or set up dlt sources and resources."
argument-hint: "[source-name]"
hooks:
  PreToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/skills/dlt/scripts/check-secrets.sh"
          timeout: 10
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

## Pipeline Types

Choose the right workflow based on your data source:

```
What kind of source?
├── REST API (JSON over HTTP)
│   └── Use: Create REST API Pipeline workflow
├── SQL Database (direct connection or SQL-over-REST)
│   ├── Direct connection (PostgreSQL, MySQL, MSSQL, etc.)
│   │   └── Use: Create SQL Database Pipeline workflow (Pattern 1)
│   └── SQL query endpoint (NetSuite SuiteQL, QuickBooks Query)
│       └── Use: Create SQL Database Pipeline workflow (Pattern 2)
└── Cloud File Storage (Azure Blob, S3, GCS, local)
    └── Use: Create Filesystem Pipeline workflow
```

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Create REST API Pipeline](workflows/create-rest-api-pipeline.md) | Loading data from a REST API — auth, pagination, incremental, column typing |
| [Create SQL Database Pipeline](workflows/create-sql-database-pipeline.md) | Loading from a database (direct connection or SQL-over-REST) |
| [Create Filesystem Pipeline](workflows/create-filesystem-pipeline.md) | Loading files from cloud storage or local filesystem |
| [Debug Pipeline](workflows/debug-pipeline.md) | Pipeline is failing — inspect state, check traces, isolate the issue |

## Common Patterns

These cross-cutting concerns apply to all pipeline types. Each workflow covers them in context, but here's a quick reference:

### Authentication
APIs use bearer tokens, API keys, OAuth2, or custom auth. dlt provides built-in auth classes for common patterns; subclass for non-standard flows. **Never hardcode credentials** — use environment variables or `dlt.secrets.value`. See [REST API workflow Step 2](workflows/create-rest-api-pipeline.md#step-2-configure-authentication).

### Pagination
Most APIs paginate results. dlt provides built-in paginators (json_link, offset, page_number, single_page). For non-standard pagination (ROWNUM wrapping, cursor-based, query-embedded), subclass `BasePaginator`. See [REST API workflow Step 3](workflows/create-rest-api-pipeline.md#step-3-configure-pagination).

### Column Typing
Prevent type inference issues by adding explicit `columns` hints to resources. Critical for: numeric fields arriving as strings, date fields stored as text, ID fields with leading zeros. See [REST API workflow Step 6](workflows/create-rest-api-pipeline.md#step-6-set-column-types).

### Incremental Loading
Track a cursor field (e.g. `modifiedDate`) to load only new/changed records. Use `lag` for APIs with eventual consistency. For file sources, track `modification_date` to skip already-processed files. See [REST API workflow Step 5](workflows/create-rest-api-pipeline.md#step-5-configure-incremental-loading).

### Processing Steps
Transform records in-flight with `map` (modify), `filter` (drop), and `yield_map` (flatten). Common uses: injecting tenant metadata, filtering soft-deleted records, flattening nested arrays. See [REST API workflow Step 4](workflows/create-rest-api-pipeline.md#step-4-define-resources).

### MCP Server

The dlt MCP server gives Claude direct access to pipeline metadata and loaded data for validation. Install by adding the following to `.mcp.json`:

```json
{
  "mcpServers": {
    "dlt": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "dlt-mcp[search]",
        "python",
        "-m",
        "dlt_mcp"
      ]
    }
  }
}
```

This runs the `dlt-mcp` package with search support via `uv` — no separate install step required. See https://dlthub.com/docs/dlt-ecosystem/llm-tooling/llm-native-workflow#install-mcp-server-optional for details.

## Anti-Patterns

- **Skipping the scaffold** — `dlt init` generates source-specific docs and a working template; starting from scratch means Claude lacks that context
- **Building all resources at once** — iterate one endpoint at a time; debugging multiple new resources simultaneously is slow and error-prone
- **Ignoring the MCP server** — querying loaded data through Claude is faster than switching to a SQL client for validation
- **Over-customising the scaffold** — the generated template is a starting point; keep it simple and let dlt handle schema inference and state management
- **Skipping column type hints** — numeric and date fields often need explicit types to prevent inference errors; add `columns` hints upfront
- **Not handling custom pagination** — if the API doesn't use standard pagination, don't force a built-in paginator; subclass `BasePaginator`
- **Hardcoding auth tokens** — credentials belong in environment variables or `.dlt/secrets.toml`, never in pipeline code

## Related Skills

- **[dbt](../dbt/SKILL.md)** — Build staging models over dlt-loaded tables
- **[dba-security](../dba-security/SKILL.md)** — Loader role permissions and raw database access controls
- **[dagster](../dagster/SKILL.md)** — Orchestrate dlt pipelines as Dagster assets

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

---
name: dlt-pipelines
description: "Write dlt/Python data ingestion pipelines. Use when a user asks to ingest data from an API, database, or file into a warehouse, create a new EL pipeline, debug a failing pipeline, or set up dlt sources and resources."
argument-hint: "[source-name]"
hooks:
  PreToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "~/.claude/skills/dlt-pipelines/scripts/check-secrets.sh"
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

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Create Pipeline](workflows/create-pipeline.md) | Building a new pipeline — init, MCP setup, iterative resource building, dbt connection |
| [Debug Pipeline](workflows/debug-pipeline.md) | Pipeline is failing — inspect state, check traces, isolate the issue |

## Anti-Patterns

- **Skipping the scaffold** — `dlt init` generates source-specific docs and a working template; starting from scratch means Claude lacks that context
- **Building all resources at once** — iterate one endpoint at a time; debugging multiple new resources simultaneously is slow and error-prone
- **Ignoring the MCP server** — querying loaded data through Claude is faster than switching to a SQL client for validation
- **Over-customising the scaffold** — the generated template is a starting point; keep it simple and let dlt handle schema inference and state management

## Related Skills

- **[dbt-staging](../dbt-staging/SKILL.md)** — Build staging models over dlt-loaded tables
- **[dbt-mcp](../dbt-mcp/SKILL.md)** — Explore loaded schemas from the dbt side
- **[analytics-architecture](../analytics-architecture/SKILL.md)** — Where dlt fits in the overall platform
- **[dba-security](../dba-security/SKILL.md)** — Loader role permissions and raw database access controls

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

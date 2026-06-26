---
name: powerbi
description: "Apply Power BI best practices. Use when a user asks to build a report, design a Power BI semantic model, write DAX measures, set up deployment pipelines, configure workspaces, connect Excel to a dataset, parameterize M queries, or plan a Power BI rollout."
---

# Power BI

## Overview

This skill encodes an opinionated Power BI methodology built around eight core tenets. It assumes data arrives as star schemas from the warehouse (via **dbt** and **dimensional-modeling**) and focuses on how to model, report, deploy, and consume that data inside the Power BI ecosystem.

Authoritative references:

- [Power BI implementation planning](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-implementation-planning-introduction)
- [Power BI guidance documentation](https://learn.microsoft.com/en-us/power-bi/guidance/)
- [Departmental BI scenario](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-implementation-planning-usage-scenario-departmental-bi)

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Design Semantic Model](workflows/design-semantic-model.md) | Planning which tables to import, model boundaries, single vs. split model decisions |
| [Build Semantic Model](workflows/build-semantic-model.md) | Creating or editing the model — M queries, relationships, DAX measures, naming conventions, donor-cloning measure suites |
| [Edit TMDL at Scale](workflows/edit-tmdl-at-scale.md) | Bulk, zero-corruption editing of PBIP/TMDL files — measure suites, model-wide rewrites — via the generate → chunk → Edit → byte-verify pipeline when the Modeling MCP isn't available |
| [Build Report](workflows/build-report.md) | Building reports against a live-connected semantic model — layout, visuals, filters, audiences |
| [Deploy and Publish](workflows/deploy-and-publish.md) | Setting up workspaces, deployment pipelines (DEV/TEST/PROD), apps, refresh schedules |
| [Connect and Consume](workflows/connect-and-consume.md) | Connecting to the semantic model from Excel or external tools instead of exporting data |

## References

Deep-dive references for file-based semantic-model work. Load the specific one your task needs.

| Reference | When to Use |
|-----------|-------------|
| [TMDL Anatomy](references/tmdl-anatomy.md) | PBIP folder layout and TMDL block grammar, UTF-8/CRLF encoding rules, `lineageTag` uniqueness, the `_Measures` insertion anchor, and paired structures (`_PrmKPI`, calculated columns) |
| [DAX Time-Intelligence Patterns](references/dax-time-intelligence-patterns.md) | Prior-period / to-date / complete-period DAX patterns, the format-mapping-by-base-type table, and the canonical ~70-variant TI suite catalog |

## Core Tenets

### 1. Separate Semantic Models from Reports

Never build reports inside the same `.pbix` file that contains the data model. Publish the semantic model as a standalone dataset, then build reports that live-connect to it. This enables multiple reports to share one governed model and prevents model drift.

### 2. One Company-Wide Semantic Model

Default to a single semantic model that serves the entire organization. Split into separate models only when forced by row-level security boundaries that cannot be expressed in a single model, or when dataset size exceeds Premium capacity limits. Every split is a conformance risk — resist it.

### 3. One App, Multiple Audiences

Create a single Power BI app per workspace and use up to 10 audience groups to control what each team sees. Do not proliferate apps — audiences are the access-control mechanism.

### 4. Deployment Pipelines (DEV / TEST / PROD)

Use Power BI deployment pipelines with three workspaces: DEV, TEST, and PROD. Requires Premium Per User (PPU) or Premium capacity. All development happens in DEV; promotion to TEST and PROD is via the pipeline — never publish directly to PROD.

### 5. Star Schemas Only

The semantic model imports `dim_*` and `fct_*` tables directly from the warehouse mart layer. Do not reshape data inside Power BI — the warehouse owns the transformation logic. If something needs to change, change it in dbt.

### 6. Don't Export — Connect

Users should never export data from Power BI to CSV/Excel for further analysis. Instead, connect Excel pivot tables to the published semantic model via a live connection. This preserves governance, keeps a single source of truth, and lets users work in their familiar tool.

### 7. Parameterized M Queries

Every M query that references a database or schema must use Power Query parameters (`DbServer`, `DbName`, `DbSchema`) so the connection can be switched across environments (DEV/TEST/PROD) without editing queries. Deployment pipelines swap parameter values automatically during promotion.

### 8. Consistent DAX Naming Conventions

DAX measure and column names must be specific and unambiguous. Avoid short or generic names like `Amount` or `Count`. Prefer descriptive names like `Total Revenue (Excl Tax)` or `Active Customer Count (30d)`. Group related measures in display folders. Use TMDL format for version-controlled definitions.

## Examples

See [examples/](examples/) for reference files:
- `semantic_model.tmdl` — Complete semantic model in TMDL format showing all framework tables, field parameters, calculation groups, and parameterized M queries

## MCP Servers

Power BI offers two MCP servers that serve different purposes. Both are in preview.

References:
- Overview: https://learn.microsoft.com/en-us/power-bi/developer/mcp/mcp-servers-overview
- Modeling MCP (GitHub): https://github.com/microsoft/powerbi-modeling-mcp
- Remote MCP setup: https://learn.microsoft.com/en-us/power-bi/developer/mcp/remote-mcp-server-get-started

### Modeling MCP Server (recommended)

Runs locally via stdio. Gives Claude direct access to create, edit, and validate semantic models — measures, relationships, columns, calculation groups, DAX queries, and TMDL files. This is the primary server for the **Build Semantic Model** and **Design Semantic Model** workflows.

**Platform:** Cross-platform — builds available for Windows, macOS (Intel + Apple Silicon), and Linux. Note that connecting to **Power BI Desktop** requires Windows (or WSL with path interop). Connecting to **Fabric workspaces** or **PBIP files** works on any platform.

**Setup:**

1. Check the [latest version](https://marketplace.visualstudio.com/items?itemName=analysis-services.powerbi-modeling-mcp) on the VS Code Marketplace
2. Download the VSIX package for your platform using the URL template:
   ```
   https://marketplace.visualstudio.com/_apis/public/gallery/publishers/analysis-services/vsextensions/powerbi-modeling-mcp/[version]/vspackage?targetPlatform=[platform]
   ```

   | Platform | `targetPlatform` value |
   |----------|----------------------|
   | Windows x64 | `win32-x64` |
   | Windows ARM | `win32-arm64` |
   | macOS Apple Silicon | `darwin-arm64` |
   | macOS Intel | `darwin-x64` |
   | Linux x64 | `linux-x64` |
   | Linux ARM64 | `linux-arm64` |

3. Rename the downloaded `.vsix` file to `.zip` and extract to a permanent location
4. Run the server executable once to verify it starts, then add to `.mcp.json`

**`.mcp.json` by platform:**

macOS / Linux:
```json
{
  "mcpServers": {
    "powerbi-modeling": {
      "command": "~/MCPServers/PowerBIModelingMCP/extension/server/powerbi-modeling-mcp",
      "args": ["--start", "--skipconfirmation"]
    }
  }
}
```

Windows (PowerShell / cmd):
```json
{
  "mcpServers": {
    "powerbi-modeling": {
      "command": "C:\\MCPServers\\PowerBIModelingMCP\\extension\\server\\powerbi-modeling-mcp.exe",
      "args": ["--start", "--skipconfirmation"]
    }
  }
}
```

WSL (calling the Windows exe via `/mnt/c/` interop):
```json
{
  "mcpServers": {
    "powerbi-modeling": {
      "command": "/mnt/c/MCPServers/PowerBIModelingMCP/extension/server/powerbi-modeling-mcp.exe",
      "args": ["--start", "--skipconfirmation"]
    }
  }
}
```

> **WSL note:** Extract the VSIX to `C:\MCPServers\` on the Windows filesystem (not inside WSL). This avoids per-user paths in `.mcp.json`, keeping the config portable across team members.

**Connection:** After setup, tell Claude which model to connect to:
- Power BI Desktop: "Connect to 'My Model' in Power BI Desktop"
- Fabric workspace: "Connect to semantic model 'Sales' in Fabric Workspace 'Production'"
- PBIP files: "Open semantic model from PBIP folder './model/definition/'"

**Key flags:**
- `--readonly` — Safe mode, prevents all write operations (good for exploration)
- `--skipconfirmation` — Auto-approves writes without prompts (recommended for Claude Code where the human-in-the-loop is the permission system)
- `--readwrite` — Default; enables writes with confirmation prompts

### Remote MCP Server

Hosted by Microsoft at `https://api.fabric.microsoft.com/v1/mcp/powerbi`. Queries published semantic models using Copilot's DAX generation engine. Useful for validating data in published models or exploring schemas without a local Power BI Desktop instance.

**Prerequisites:**
- Power BI admin must enable the tenant setting: *"Users can use the Power BI Model Context Protocol server endpoint (preview)"*
- Build permissions on the target semantic model
- Copilot license (required for the Generate Query tool — can be disabled if you only need schema + execute)

**Setup:** Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "powerbi-remote": {
      "type": "http",
      "url": "https://api.fabric.microsoft.com/v1/mcp/powerbi"
    }
  }
}
```

> **Note:** The Remote MCP uses HTTP transport. Verify your MCP client supports HTTP-based servers — not all do. Claude Code supports this via the `type: "http"` configuration.

**Authentication:** No environment variables needed — the server authenticates via browser-based Microsoft OAuth when first invoked. Queries execute under the authenticated user's permissions, and row-level security (RLS) is enforced.

**Semantic model ID:** Every tool call requires a semantic model ID. Find it in the Power BI service URL:

```
https://app.powerbi.com/groups/{workspaceId}/datasets/{semanticModelId}
```

To avoid providing the ID every session, store frequently used IDs in a project file (e.g., `.claude/memory/powerbi-models.md`) or reference them in your CLAUDE.md:

```markdown
## Power BI Semantic Models
- Sales Model: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- Finance Model: `f9e8d7c6-b5a4-3210-fedc-ba0987654321`
```

**Available tools:**
- **Get Semantic Model Schema** — Retrieves tables, columns, measures, relationships, and AI metadata
- **Generate Query** — Converts natural language to optimized DAX (requires Copilot license)
- **Execute Query** — Runs a DAX query and returns results

### Which server to use

| Scenario | Server |
|----------|--------|
| Building or editing a semantic model (measures, relationships, columns) | Modeling |
| Validating DAX queries during development | Modeling |
| Querying a published model to check data after deployment | Remote |
| Exploring a model schema without Power BI Desktop | Remote |
| Working with TMDL / Power BI Project files | Modeling |

Start with the **Modeling MCP server** — it covers the full build-and-validate cycle and runs on all platforms. Add the Remote server when you need to query published production models or leverage Copilot's DAX generation.

## Anti-Patterns

- **Model inside the report .pbix** — Couples the dataset to a single report. Every new report duplicates the model, causing refresh sprawl and governance drift.
- **Multiple semantic models for the same data** — Creates conflicting metric definitions. One model, one truth.
- **Publishing directly to PROD** — Bypasses testing. Always promote through the deployment pipeline.
- **Reshaping data in Power Query** — If you need a new column or join, add it in dbt. Power BI should import clean star schemas, not rebuild them.
- **Exporting to CSV/Excel** — Breaks the single source of truth. Connect instead of exporting.
- **Hardcoded server/database in M queries** — Breaks environment promotion. Always parameterize.
- **Ambiguous DAX names** — `Revenue` could mean gross, net, or adjusted. Be explicit: `Total Revenue (Gross)`.
- **One app per team** — Creates fragmentation. Use one app with audience groups instead.

## Related Skills

- **[dimensional-modeling](../dimensional-modeling/SKILL.md)** — Star schema design decisions that determine what the semantic model imports
- **[dbt](../dbt/SKILL.md)** — The transformation layer that produces the `dim_*` and `fct_*` mart tables consumed by the semantic model
- **[dagster](../dagster/SKILL.md)** — Orchestrate Power BI semantic model refreshes via Dagster

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

# swishbot

[![CI](https://github.com/swishbi/swishbot/actions/workflows/ci.yml/badge.svg)](https://github.com/swishbi/swishbot/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)

A Claude Code plugin that distributes data stack skills, agents, and project scaffolding for [Swish BI](swishbi.com). Install once — get 9 skills, 3 agents, hooks, MCP servers, and slash commands.

## Quick Start

```bash
# Add the swishbot marketplace
/plugin marketplace add swishbi/swishbot

# Install the plugin
/plugin install swishbot@swishbot

# Everything is now available:
# - 8 skills auto-loaded
# - 3 agents in /agents
# - Hooks active
# - MCP servers configured

# Scaffold a new project
/swishbot:scaffold my-client-project

# Set up project config
/swishbot:init-project
/swishbot:init-memory
```

No `pip install`. No Python dependency. Pure Claude Code native.

## Zero-Touch Team Onboarding

Add this to your project's `.claude/settings.json` (checked into version control):

```json
{
  "extraKnownMarketplaces": {
    "swishbot": {
      "source": {
        "source": "github",
        "repo": "swishbi/swishbot",
        "ref": "stable"
      }
    }
  },
  "enabledPlugins": {
    "swishbot@swishbot": true
  }
}
```

New team members clone the repo, open with Claude Code, and are prompted to accept the plugin. No manual steps.

## Available Skills

### Discovery & Planning
| Skill | Description | Status |
|-------|-------------|--------|
| `requirements-discovery` | Act as a business analyst — stakeholder discovery, SME interviews, and column-level logic mapping | :white_check_mark: |

### Infrastructure
| Skill | Description | Status |
|-------|-------------|--------|
| `dba-security` | DBA security practices | :white_check_mark: |
| `iac-terraform` | Deploying infrastructure using Terraform/IaC | :white_check_mark: |

### Ingestion
| Skill | Description | Status |
|-------|-------------|--------|
| `dlt` | Writing dlt/Python ingestion pipelines | :white_check_mark: |

### Orchestration
| Skill | Description | Status |
|-------|-------------|--------|
| `dagster` | Orchestrate data pipelines with Dagster and Dagster+ | :white_check_mark: |

### Transformation
| Skill | Description | Status |
|-------|-------------|--------|
| `dbt` | All dbt layers — staging, intermediate, marts, SQL conventions, MCP tooling | :white_check_mark: |
| `dimensional-modeling` | Dimensional modeling best practices | :white_check_mark: |

### Analytics & Presentation
| Skill | Description | Status |
|-------|-------------|--------|
| `powerbi` | Power BI best practices | :white_check_mark: |

### Documentation
| Skill | Description | Status |
|-------|-------------|--------|
| `tech-docs` | Write technical documentation — setup guides, runbooks, data dictionaries, pipeline READMEs, architecture notes | :white_check_mark: |

## Available Agents

Agents are persona definitions that compose multiple skills into roles. Install the plugin to get all agents automatically.

| Agent | Description | Skills Composed |
|-------|-------------|-----------------|
| `business-analyst` | Guides stakeholders from idea to implementation-ready spec; validates sources with dbt MCP and inspects Power BI assets | requirements-discovery, dbt, powerbi |
| `data-engineer` | Builds the full data stack end to end — dlt ingestion, Dagster orchestration, dbt transformation, dimensional schema design, and Power BI semantic models | dlt, dba-security, dagster, dbt, dimensional-modeling, powerbi |
| `platform-engineer` | Sets up infrastructure, security, and platform architecture | dagster, iac-terraform, dba-security |

## Slash Commands

| Command | Description |
|---------|-------------|
| `/swishbot:scaffold <name>` | Scaffold a complete analytics project with ingestion, transformation, and orchestration layers |
| `/swishbot:init-project` | Install a starter CLAUDE.md and SECURITY.md into your project |
| `/swishbot:init-memory` | Scaffold shared project memory directory with cross-agent templates |
| `/swishbot:migrate [dir]` | Migrate an existing dlt + dbt project into the swishbot structure with Dagster orchestration |

## How It Works

swishbot is a **Claude Code plugin** — a self-contained package that bundles skills, agents, hooks, MCP servers, and slash commands. When installed via `claude plugin install`, everything auto-loads into your Claude Code sessions.

Skills are designed to be platform-agnostic at the methodology level — they encode *how to think about the problem*, and Claude applies that reasoning to whatever platform you're working on (Snowflake, BigQuery, Databricks, etc.).

## Project Structure

```
swishbot/
├── .claude-plugin/
│   └── marketplace.json              # Marketplace catalog
├── plugins/
│   └── swishbot/                     # The plugin
│       ├── .claude-plugin/
│       │   └── plugin.json           # Plugin manifest
│       ├── skills/                   # All 9 skills
│       │   ├── dbt/
│       │   │   ├── SKILL.md
│       │   │   ├── workflows/
│       │   │   ├── references/
│       │   │   ├── scripts/
│       │   │   └── examples/
│       │   ├── dagster/
│       │   ├── dlt/
│       │   ├── dimensional-modeling/
│       │   ├── powerbi/
│       │   ├── requirements-discovery/
│       │   ├── dba-security/
│       │   ├── iac-terraform/
│       │   └── tech-docs/
│       ├── agents/                   # All 3 agents
│       │   ├── data-engineer.md
│       │   ├── business-analyst.md
│       │   └── platform-engineer.md
│       ├── commands/                 # Slash commands
│       │   ├── scaffold.md
│       │   ├── init-project.md
│       │   ├── init-memory.md
│       │   └── migrate.md
│       ├── hooks/
│       │   └── hooks.json            # Merged hooks from all skills
│       ├── .mcp.json                 # MCP servers (dbt, dagster, dlt, powerbi)
│       ├── templates/                # Scaffold templates
│       │   └── memory/              # Memory templates
│       ├── CLAUDE.md                 # Starter project config
│       └── SECURITY.md              # Security policy
├── tests/
│   └── test_plugin.py               # Plugin validation tests
├── docs/
├── README.md
└── pyproject.toml                    # Dev/test dependencies only
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and how to create new skills.

## License

Proprietary — Copyright (c) 2026 Swish BI Limited. All rights reserved.

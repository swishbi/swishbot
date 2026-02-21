# swishbot

[![CI](https://github.com/swishbi/swishbot/actions/workflows/ci.yml/badge.svg)](https://github.com/swishbi/swishbot/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)

A distributable skill and agent library for [Swish BI](swishbi.com). Install skills and agents into your Claude environment with a single command.

## Quick Start

```bash
# Install swishbot
pip install swishbot

# List available skills
swishbot list

# Install a skill into your Claude project
swishbot install dbt

# Install a skill to a custom path
swishbot install dbt --path ~/.claude/skills

# Install all skills
swishbot install --all

# Install an agent
swishbot install --agent analytics-engineer

# Install all agents
swishbot install --agent --all

# Scaffold a new analytics project
swishbot scaffold my-client-project

# Add a starter CLAUDE.md to your project
swishbot init-project

# Overwrite an existing CLAUDE.md
swishbot init-project --force

# List hooks provided by installed skills
swishbot hooks

# Scaffold project memory directory
swishbot init-memory
```

## Available Skills

### Discovery & Planning
| Skill | Description | Status |
|-------|-------------|--------|
| `business-logic-mapping` | Map tribal knowledge from SMEs into implementation-ready business logic tied to staging columns | :white_check_mark: |
| `requirements-discovery` | Act as a business analyst to guide stakeholders from idea to implementation-ready requirements | :white_check_mark: |

### Infrastructure
| Skill | Description | Status |
|-------|-------------|--------|
| `dba-security` | DBA security practices | :white_check_mark: |
| `iac-terraform` | Deploying infrastructure using Terraform/IaC | :x: |

### Ingestion
| Skill | Description | Status |
|-------|-------------|--------|
| `dlt-pipelines` | Writing dlt/Python ingestion pipelines | :white_check_mark: |

### Orchestration
| Skill | Description | Status |
|-------|-------------|--------|
| `dagster` | Orchestrate data pipelines with Dagster and Dagster+ | :white_check_mark: |

### Transformation (dbt)
| Skill | Description | Status |
|-------|-------------|--------|
| `dbt` | All dbt layers — staging, intermediate, marts, SQL conventions, MCP tooling | :white_check_mark: |
| `dimensional-modeling` | Dimensional modeling best practices | :white_check_mark: |

### Analytics & Presentation
| Skill | Description | Status |
|-------|-------------|--------|
| `powerbi` | Power BI best practices | :white_check_mark: |
| `semantic-layer` | Building the semantic layer | :x: |

## Available Agents

Agents are persona definitions that compose multiple skills into roles. Install an agent to give Claude a focused identity for a specific type of work.

| Agent | Description | Skills Composed |
|-------|-------------|-----------------|
| `analytics-engineer` | Designs dimensional schemas and builds dbt models across all layers with MCP tooling | dbt, dimensional-modeling |
| `business-analyst` | Guides stakeholders from idea to implementation-ready spec; validates sources with dbt MCP | requirements-discovery, business-logic-mapping, dbt |
| `data-engineer` | Builds ingestion pipelines with proper security | dlt-pipelines, dba-security |
| `platform-engineer` | Sets up infrastructure, security, and platform architecture | dagster, iac-terraform, dba-security |

## How It Works

Each skill is a self-contained directory with a `SKILL.md` file that Claude reads to understand how to execute the work. Agents are persona definitions (`AGENT.md`) that compose multiple skills into a role. When you run `swishbot install <skill>` or `swishbot install --agent <agent>`, it copies the directory into your Claude configuration so it's available in your sessions.

Skills are designed to be platform-agnostic at the methodology level — they encode *how to think about the problem*, and Claude applies that reasoning to whatever platform you're working on (Snowflake, BigQuery, Databricks, etc.).

## Project Structure

```
swishbot/
├── pyproject.toml
├── SECURITY.md                  # Contributor security policy
├── .github/
│   └── workflows/
│       └── ci.yml               # CI: lint, format, test
├── src/
│   └── swishbot/
│       ├── __init__.py
│       ├── cli.py               # CLI logic
│       ├── scaffold_templates/  # Templates for scaffold command
│       ├── memory_templates/    # Templates for init-memory
│       │   ├── MEMORY.md
│       │   ├── conventions.md
│       │   ├── modeling-decisions.md
│       │   └── source-catalog.md
│       └── .claude/             # Mirrors ~/.claude/ install target
│           ├── CLAUDE.md        # Starter project config
│           ├── SECURITY.md      # User-facing security policy
│           ├── agents/          # Agent persona definitions
│           │   ├── analytics-engineer/
│           │   │   └── AGENT.md
│           │   ├── business-analyst/
│           │   │   └── AGENT.md
│           │   ├── data-engineer/
│           │   │   └── AGENT.md
│           │   └── platform-engineer/
│           │       └── AGENT.md
│           └── skills/
│               ├── dbt/
│               │   ├── SKILL.md         # Behavioral guide + router
│               │   ├── workflows/       # Step-by-step procedures
│               │   │   ├── staging/
│               │   │   │   ├── create-staging-source.md
│               │   │   │   ├── transform-staging-models.md
│               │   │   │   └── validate-staging-models.md
│               │   │   ├── intermediate/
│               │   │   │   ├── create-intermediate-model.md
│               │   │   │   └── refactor-to-intermediate.md
│               │   │   └── marts/
│               │   │       ├── create-mart-model.md
│               │   │       └── create-incremental-mart.md
│               │   ├── references/      # Reference documentation
│               │   │   ├── style-and-conventions.md
│               │   │   ├── mcp-setup-and-tools.md
│               │   │   ├── loader-metadata.md
│               │   │   └── staging-sql-conventions.md
│               │   ├── scripts/         # Hook scripts
│               │   │   └── check-source-yaml.sh
│               │   └── examples/
│               ├── dagster/
│               │   ├── SKILL.md         # Router: project setup + component workflows
│               │   ├── workflows/
│               │   │   ├── setup-project.md
│               │   │   ├── add-dlt-component.md
│               │   │   ├── add-dbt-component.md
│               │   │   └── add-custom-component.md
│               │   └── examples/
│               ├── dlt-pipelines/
│               │   ├── SKILL.md
│               │   └── scripts/
│               │       └── check-secrets.sh
│               ├── dimensional-modeling/
│               │   ├── SKILL.md
│               │   └── examples/
│               ├── business-logic-mapping/
│               │   └── SKILL.md
│               ├── requirements-discovery/
│               │   └── SKILL.md
│               ├── dba-security/
│               │   ├── SKILL.md
│               │   ├── scripts/
│               │   │   └── validate-sql.sh
│               │   └── examples/
│               ├── iac-terraform/
│               │   └── SKILL.md
│               ├── semantic-layer/
│               │   └── SKILL.md
│               └── powerbi/
│                   ├── SKILL.md         # Router: tenets + workflow index
│                   ├── workflows/       # Step-by-step procedures
│                   │   ├── design-semantic-model.md
│                   │   ├── build-semantic-model.md
│                   │   ├── build-report.md
│                   │   ├── deploy-and-publish.md
│                   │   └── connect-and-consume.md
│                   └── examples/
│                       └── semantic_model.tmdl
└── tests/
    └── test_cli.py              # CLI test suite
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and how to create new skills.

## License

Proprietary — Copyright (c) 2026 Swish BI Limited. All rights reserved.

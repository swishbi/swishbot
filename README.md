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
swishbot install dbt-staging

# Install a skill to a custom path
swishbot install dbt-staging --path ~/.claude/skills

# Install all skills
swishbot install --all

# Install an agent
swishbot install --agent data-modeler

# Install all agents
swishbot install --agent --all

# Add a starter CLAUDE.md to your project
swishbot init-project

# Overwrite an existing CLAUDE.md
swishbot init-project --force
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
| `analytics-architecture` | Analytics reference architecture | :x: |
| `dba-security` | DBA security practices | :white_check_mark: |
| `iac-terraform` | Deploying infrastructure using Terraform/IaC | :x: |

### Ingestion
| Skill | Description | Status |
|-------|-------------|--------|
| `dlt-pipelines` | Writing dlt/Python ingestion pipelines | :white_check_mark: |

### Transformation (dbt)
| Skill | Description | Status |
|-------|-------------|--------|
| `dbt-intermediate` | Building the intermediate/silver layer | :white_check_mark: |
| `dbt-marts` | Building the mart/gold layer | :white_check_mark: |
| `dbt-mcp` | Configure and use the dbt MCP server with Claude | :white_check_mark: |
| `dbt-staging` | Building the staging/bronze layer | :white_check_mark: |
| `dbt-staging-model` | Conventions for writing a dbt staging model SQL file | :white_check_mark: |
| `dbt-style` | Cross-cutting dbt style, naming, and project structure conventions | :white_check_mark: |
| `dimensional-modeling` | Dimensional modeling best practices | :white_check_mark: |

### Analytics & Presentation
| Skill | Description | Status |
|-------|-------------|--------|
| `powerbi` | Power BI best practices | :x: |
| `semantic-layer` | Building the semantic layer | :x: |

## Available Agents

Agents are persona definitions that compose multiple skills into roles. Install an agent to give Claude a focused identity for a specific type of work.

| Agent | Description | Skills Composed |
|-------|-------------|-----------------|
| `analytics-engineer` | Builds dbt models across all layers with MCP tooling | dbt-staging, dbt-staging-model, dbt-intermediate, dbt-marts, dbt-style, dbt-mcp |
| `business-analyst` | Guides stakeholders from idea to implementation-ready spec | requirements-discovery, business-logic-mapping |
| `data-engineer` | Builds ingestion pipelines with proper security | dlt-pipelines, dba-security |
| `data-modeler` | Designs and builds dimensional models across the full dbt DAG | dbt-staging, dbt-staging-model, dbt-intermediate, dbt-marts, dbt-style, dimensional-modeling |
| `platform-engineer` | Sets up infrastructure, security, and platform architecture | analytics-architecture, iac-terraform, dba-security |

## How It Works

Each skill is a self-contained directory with a `SKILL.md` file that Claude reads to understand how to execute the work. Agents are persona definitions (`AGENT.md`) that compose multiple skills into a role. When you run `swishbot install <skill>` or `swishbot install --agent <agent>`, it copies the directory into your Claude configuration so it's available in your sessions.

Skills are designed to be platform-agnostic at the methodology level — they encode *how to think about the problem*, and Claude applies that reasoning to whatever platform you're working on (Snowflake, BigQuery, Databricks, etc.).

## Project Structure

```
swishbot/
├── pyproject.toml
├── .github/
│   └── workflows/
│       └── ci.yml               # CI: lint, format, test
├── src/
│   └── swishbot/
│       ├── __init__.py
│       ├── cli.py               # CLI logic
│       └── .claude/             # Mirrors ~/.claude/ install target
│           ├── CLAUDE.md        # Starter project config
│           ├── agents/          # Agent persona definitions
│           │   ├── analytics-engineer/
│           │   │   └── AGENT.md
│           │   ├── business-analyst/
│           │   │   └── AGENT.md
│           │   ├── data-engineer/
│           │   │   └── AGENT.md
│           │   ├── data-modeler/
│           │   │   └── AGENT.md
│           │   └── platform-engineer/
│           │       └── AGENT.md
│           └── skills/
│               ├── dbt-staging/
│               │   ├── SKILL.md         # Router: overview + workflow index
│               │   ├── workflows/       # Step-by-step procedures
│               │   │   ├── create-staging-source.md
│               │   │   ├── transform-staging-models.md
│               │   │   └── validate-staging-models.md
│               │   └── examples/
│               ├── dbt-staging-model/
│               │   ├── SKILL.md
│               │   └── examples/
│               ├── dbt-style/
│               │   └── SKILL.md
│               ├── dbt-intermediate/
│               │   └── SKILL.md
│               ├── dbt-marts/
│               │   └── SKILL.md
│               ├── dbt-mcp/
│               │   └── SKILL.md
│               ├── dlt-pipelines/
│               │   └── SKILL.md
│               ├── dimensional-modeling/
│               │   ├── SKILL.md
│               │   └── examples/
│               ├── business-logic-mapping/
│               │   └── SKILL.md
│               ├── requirements-discovery/
│               │   └── SKILL.md
│               ├── analytics-architecture/
│               │   └── SKILL.md
│               ├── dba-security/
│               │   ├── SKILL.md
│               │   └── examples/
│               ├── iac-terraform/
│               │   └── SKILL.md
│               ├── semantic-layer/
│               │   └── SKILL.md
│               └── powerbi/
│                   └── SKILL.md
└── tests/
    └── test_cli.py              # CLI test suite
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and how to create new skills.

## License

Proprietary — Copyright (c) 2026 Swish BI Limited. All rights reserved.

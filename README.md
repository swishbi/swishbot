# swishbot

[![CI](https://github.com/swishbi/swishbot/actions/workflows/ci.yml/badge.svg)](https://github.com/swishbi/swishbot/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)

A distributable skill library for [Swish BI](swishbi.com). Install skills into your Claude environment with a single command.

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
| `dimensional-modeling` | Dimensional modeling best practices | :x: |

### Analytics & Presentation
| Skill | Description | Status |
|-------|-------------|--------|
| `powerbi` | Power BI best practices | :x: |
| `semantic-layer` | Building the semantic layer | :x: |

## How It Works

Each skill is a self-contained directory with a `SKILL.md` file that Claude reads to understand how to execute the work. When you run `swishbot install <skill>`, it copies the skill directory into your Claude configuration so it's available in your sessions.

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
│       ├── CLAUDE.md            # Starter project config
│       └── skills/
│           ├── iac-terraform/
│           │   └── SKILL.md
│           ├── dlt-pipelines/
│           │   └── SKILL.md
│           ├── dbt-style/
│           │   └── SKILL.md
│           ├── dbt-staging/
│           │   ├── SKILL.md
│           │   └── examples/
│           ├── dbt-staging-model/
│           │   ├── SKILL.md
│           │   └── examples/
│           ├── dbt-intermediate/
│           │   └── SKILL.md
│           ├── dbt-marts/
│           │   └── SKILL.md
│           ├── dbt-mcp/
│           │   └── SKILL.md
│           ├── business-logic-mapping/
│           │   └── SKILL.md
│           ├── requirements-discovery/
│           │   └── SKILL.md
│           ├── dimensional-modeling/
│           │   └── SKILL.md
│           ├── dba-security/
│           │   ├── SKILL.md
│           │   └── examples/
│           ├── analytics-architecture/
│           │   └── SKILL.md
│           ├── semantic-layer/
│           │   └── SKILL.md
│           └── powerbi/
│               └── SKILL.md
└── tests/
    └── test_cli.py              # CLI test suite
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and how to create new skills.

## License

Proprietary — Copyright (c) 2026 Swish BI Limited. All rights reserved.

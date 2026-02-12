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

# Or install in dev mode from source
pip install -e .

# Install with test/dev dependencies
pip install -e ".[test]"

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

### Ingestion & Infrastructure
| Skill | Description | Status |
|-------|-------------|--------|
| `iac-terraform` | Deploying infrastructure using Terraform/IaC | :x: |
| `dlt-pipelines` | Writing dlt/Python ingestion pipelines | :x: |

### Transformation (dbt)
| Skill | Description | Status |
|-------|-------------|--------|
| `dbt-staging` | Building the staging/bronze layer | :x: |
| `dbt-intermediate` | Building the intermediate/silver layer | :x: |
| `dbt-marts` | Building the mart/gold layer | :x: |

### Modeling & Security
| Skill | Description | Status |
|-------|-------------|--------|
| `dimensional-modeling` | Dimensional modeling best practices | :x: |
| `dba-security` | DBA security practices | :x: |

### Analytics & Presentation
| Skill | Description | Status |
|-------|-------------|--------|
| `analytics-architecture` | Analytics reference architecture | :x: |
| `semantic-layer` | Building the semantic layer | :x: |
| `powerbi` | Power BI best practices | :x: |

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
│           ├── dbt-staging/
│           │   └── SKILL.md
│           ├── dbt-intermediate/
│           │   └── SKILL.md
│           ├── dbt-marts/
│           │   └── SKILL.md
│           ├── dimensional-modeling/
│           │   └── SKILL.md
│           ├── dba-security/
│           │   └── SKILL.md
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

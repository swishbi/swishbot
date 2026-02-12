# swishbot

A distributable skill library for [Swish BI](swishbi.com). Install skills into your Claude environment with a single command.

## Quick Start

```bash
# Install swishbot
pip install swishbot

# Or install in dev mode from source
pip install -e .

# List available skills
swishbot list

# Install a skill into your Claude project
swishbot install dbt-staging

# Install a skill to a custom path
swishbot install dbt-staging --path ~/.claude/skills

# Install all skills
swishbot install --all
```

## Available Skills

### Ingestion & Infrastructure
| Skill | Description |
|-------|-------------|
| `iac-terraform` | Deploying infrastructure using Terraform/IaC |
| `dlt-pipelines` | Writing dlt/Python ingestion pipelines |

### Transformation (dbt)
| Skill | Description |
|-------|-------------|
| `dbt-staging` | Building the staging/bronze layer |
| `dbt-intermediate` | Building the intermediate/silver layer |
| `dbt-marts` | Building the mart/gold layer |

### Modeling & Security
| Skill | Description |
|-------|-------------|
| `dimensional-modeling` | Dimensional modeling best practices |
| `dba-security` | DBA security practices |

### Analytics & Presentation
| Skill | Description |
|-------|-------------|
| `analytics-architecture` | Analytics reference architecture |
| `semantic-layer` | Building the semantic layer |
| `powerbi` | Power BI best practices |

## How It Works

Each skill is a self-contained directory with a `SKILL.md` file that Claude reads to understand how to execute the work. When you run `swishbot install <skill>`, it copies the skill directory into your Claude configuration so it's available in your sessions.

Skills are designed to be platform-agnostic at the methodology level — they encode *how to think about the problem*, and Claude applies that reasoning to whatever platform you're working on (Snowflake, BigQuery, Databricks, etc.).

## Project Structure

```
swishbot/
├── pyproject.toml
├── src/
│   └── swishbot/
│       ├── __init__.py
│       ├── cli.py                   # CLI logic
│       └── skills/
    ├── iac-terraform/
    │   ├── SKILL.md
    │   ├── references/          # Optional: examples, templates
    │   └── scripts/             # Optional: helper scripts
    ├── dlt-pipelines/
    │   └── SKILL.md
    ├── dbt-staging/
    │   └── SKILL.md
    ├── dbt-intermediate/
    │   └── SKILL.md
    ├── dbt-marts/
    │   └── SKILL.md
    ├── dimensional-modeling/
    │   └── SKILL.md
    ├── dba-security/
    │   └── SKILL.md
    ├── analytics-architecture/
    │   └── SKILL.md
    ├── semantic-layer/
    │   └── SKILL.md
    └── powerbi/
        └── SKILL.md
```

## Developing Skills

### Creating a new skill

```bash
swishbot init my-new-skill
```

This scaffolds a new skill directory with a SKILL.md template.

### Testing a skill

Point Claude Code at the skill and run it against a real scenario. Iterate on the SKILL.md until Claude produces correct output on the first shot.

### Skill anatomy

Every skill has at minimum a `SKILL.md` with this structure:

```markdown
---
name: skill-name
description: "When to use this skill and what it does."
---

# Skill Title

## Overview
What this skill does and the methodology behind it.

## [Your methodology sections]
The opinionated guidance that makes Claude work like you.
```

Optional additions:
- `references/` — examples, templates, lookup tables
- `scripts/` — helper scripts the skill can invoke

## License

Proprietary — [Your consultancy name]

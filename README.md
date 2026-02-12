# swishbot

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

Proprietary — [Your consultancy name]

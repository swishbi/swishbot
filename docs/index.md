# swishbot

A distributable skill library for [Swish BI](https://swishbi.com). Install skills into your Claude environment with a single command.

## What is swishbot?

swishbot distributes self-contained **skills** — opinionated methodology guides that Claude reads to understand how to execute data engineering and analytics work.

Each skill encodes *how to think about the problem*, not platform-specific implementation details. Claude already knows the platforms (Snowflake, BigQuery, Databricks, etc.) — skills teach it how **you** think.

## Quick start

```bash
# Install swishbot
pip install swishbot

# See what's available
swishbot list

# Install a skill
swishbot install dbt-staging

# Install all skills
swishbot install --all

# Add a starter CLAUDE.md to your project
swishbot init-project
```

## How it works

1. **Install swishbot** — `pip install swishbot`
2. **Install skills** — `swishbot install <skill>` copies skill files to `~/.claude/skills/`
3. **Init your project** — `swishbot init-project` creates a `CLAUDE.md` that references your installed skills
4. **Work with Claude** — Claude reads the skills and applies the methodology to your project

Skills are platform-agnostic at the methodology level. They encode consistent, best-practices guidance that Claude applies to whatever stack you're working with.

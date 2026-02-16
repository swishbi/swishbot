# swishbot

A distributable skill and agent library for [Swish BI](https://swishbi.com). Install skills and agents into your Claude environment with a single command.

## What is swishbot?

swishbot distributes self-contained **skills** and **agents** for data engineering and analytics work.

**Skills** are opinionated methodology guides that Claude reads to understand how to execute specific tasks. Each skill encodes *how to think about the problem*, not platform-specific implementation details. Claude already knows the platforms (Snowflake, BigQuery, Databricks, etc.) — skills teach it how **you** think.

**Agents** are persona definitions that compose multiple skills into a focused role (e.g., data-modeler, analytics-engineer). Install an agent to give Claude a specific identity for a type of work.

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

# Install an agent
swishbot install --agent data-modeler

# Add a starter CLAUDE.md to your project
swishbot init-project
```

## How it works

1. **Install swishbot** — `pip install swishbot`
2. **Install skills** — `swishbot install <skill>` copies skill files to `~/.claude/skills/`
3. **Install agents** — `swishbot install --agent <agent>` copies agent files to `~/.claude/agents/`
4. **Init your project** — `swishbot init-project` creates a `CLAUDE.md` that references your installed skills and agents
5. **Work with Claude** — Claude reads the skills and applies the methodology to your project

Skills are platform-agnostic at the methodology level. They encode consistent, best-practices guidance that Claude applies to whatever stack you're working with.

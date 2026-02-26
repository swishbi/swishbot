# swishbot

A Claude Code plugin that distributes data stack skills, agents, and project scaffolding for [Swish BI](https://swishbi.com). Install once — get 8 skills, 4 agents, hooks, MCP servers, and slash commands.

## What is swishbot?

swishbot distributes self-contained **skills**, **agents**, **hooks**, **MCP servers**, and **slash commands** for data engineering and analytics work.

**Skills** are opinionated methodology guides that Claude reads to understand how to execute specific tasks. Each skill encodes *how to think about the problem*, not platform-specific implementation details. Claude already knows the platforms (Snowflake, BigQuery, Databricks, etc.) — skills teach it how **you** think.

**Agents** are persona definitions that compose multiple skills into a focused role (e.g., analytics-engineer, data-engineer). They give Claude a specific identity for a type of work.

**Hooks** enforce rules automatically — SQL validation, credential checks, and more — without any manual setup.

**MCP servers** connect Claude to external tools like dbt, Dagster, dlt, and Power BI.

## Quick start

=== "Claude Code"

    ```bash
    # Add the swishbot marketplace
    /plugin marketplace add swishbi/swishbot

    # Install the plugin
    /plugin install swishbot@swishbot
    ```

=== "skills.sh"

    ```bash
    npx skills add swishbi/swishbot
    ```

    Follow the interactive prompts to install.

Everything is now available:

- 8 skills auto-loaded
- 4 agents in `/agents`
- Hooks active
- MCP servers configured

```bash
# Scaffold a new project
/swishbot:scaffold my-client-project

# Set up project config
/swishbot:init-project
/swishbot:init-memory
```

No `pip install`. No Python dependency. Pure Claude Code native.

## How it works

1. **Install the plugin** — via skills.sh or native Claude Code commands
2. **Skills, agents, hooks, and MCP servers auto-load** — no per-skill install step
3. **Use slash commands** — `/swishbot:scaffold`, `/swishbot:init-project`, `/swishbot:init-memory`, `/swishbot:migrate`
4. **Work with Claude** — Claude reads the skills and applies the methodology to your project

Skills are platform-agnostic at the methodology level. They encode consistent, best-practices guidance that Claude applies to whatever stack you're working with.

## Zero-touch team onboarding

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

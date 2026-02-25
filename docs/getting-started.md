# Getting Started

## Install the plugin

=== "skills.sh"

    ```bash
    npx skills add swishbi/swishbot
    ```

    Follow the interactive prompts to install the plugin.

=== "Claude Code"

    ```bash
    # Add the swishbot marketplace
    /plugin marketplace add swishbi/swishbot

    # Install the plugin
    /plugin install swishbot@swishbot
    ```

Both paths result in the same outcome: the plugin is installed and all skills, agents, hooks, and MCP servers auto-load.

## Zero-touch team onboarding

For teams, add this to your project's `.claude/settings.json` (checked into version control):

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

## What you get

| Component | Count | Description |
|-----------|-------|-------------|
| Skills | 8 | dbt, dagster, dlt, dimensional-modeling, powerbi, requirements-discovery, dba-security, iac-terraform |
| Agents | 4 | analytics-engineer, data-engineer, business-analyst, platform-engineer |
| Hooks | Auto | SQL validation, credential checks, Terraform validation |
| MCP servers | 4 | dbt, dagster, dlt, powerbi |
| Slash commands | 3 | scaffold, init-project, init-memory |

## Set up your project

Generate a starter `CLAUDE.md` and `SECURITY.md` in your project directory:

```bash
/swishbot:init-project
```

This creates files that:

- Define project conventions
- Describe your project structure and platform environment
- Provide security guidelines for SQL safety, credential handling, and prompt injection defense

Edit `CLAUDE.md` to fill in your project details. Claude reads this file to understand your project context and apply the right skill guidance.

## Set up project memory

Scaffold a memory directory so Claude can persist modeling decisions, source metadata, and conventions across sessions:

```bash
/swishbot:init-memory
```

This creates `.claude/memory/` with template files and a session-end hook. There are two distinct memory systems at work:

- **Per-agent memory** — Each agent (analytics-engineer, data-engineer, etc.) automatically manages its own `.claude/agent-memory/<agent-name>/` directory via `memory: project`. No setup needed.
- **Shared project memory** — `/swishbot:init-memory` creates `.claude/memory/` for cross-agent decisions (naming conventions, modeling choices, source quirks) that all agents read and contribute to.

After running `init-memory`, uncomment the `@` import in your `CLAUDE.md` to also load shared memory into the main Claude session:

```markdown
@.claude/memory/MEMORY.md
```

See [Commands & Setup](commands-and-setup.md#memory-architecture) for the full memory architecture.

## Scaffold a new project

Create a complete analytics project with ingestion, transformation, orchestration, and CI/CD:

```bash
/swishbot:scaffold my-client-project
```

See [Commands & Setup](commands-and-setup.md#scaffold) for what gets created.

## Verify it works

Open Claude Code in your project. Skills auto-load from the plugin — Claude will automatically apply the methodology when working on relevant tasks. Try asking Claude to build a dbt model or write a dlt pipeline.

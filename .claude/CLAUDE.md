# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

swishbot is a Claude Code plugin that distributes "skills" and "agents" for data engineering work. Skills are opinionated methodology guides; agents are persona definitions that compose multiple skills into roles (e.g., data-engineer, platform-engineer). The repo is structured as a **monorepo marketplace** containing a single plugin.

## Commands

```bash
# Install dev environment (uses uv for package management)
uv sync --extra test

# Lint and format
uv run ruff check tests/ docs/
uv run ruff format tests/ docs/

# Run all tests
uv run pytest -v

# Run a single test
uv run pytest -v tests/test_plugin.py::test_function_name
```

## Architecture

The repo is a **marketplace** (`.claude-plugin/marketplace.json`) containing one **plugin** (`plugins/swishbot/`). No Python CLI — everything is native Claude Code.

### Plugin Structure (`plugins/swishbot/`)

- **`skills/`** — 8 skill directories, each with `SKILL.md` (YAML frontmatter + methodology content) and optional `workflows/`, `examples/`, `scripts/`, `references/` subdirectories
- **`agents/`** — 3 agent markdown files with YAML frontmatter (`name`, `description`, `model`, `color`, `skills`, `mcpServers`, `memory`) and persona content
- **`commands/`** — 3 slash commands (`scaffold.md`, `init-project.md`, `init-memory.md`) that replace the old CLI subcommands
- **`hooks/hooks.json`** — Merged hooks from all skills (PreToolUse, PostToolUse, Stop events)
- **`.mcp.json`** — MCP server definitions (dbt, dagster, dlt, powerbi)
- **`templates/`** — Scaffold template files for project generation; `templates/memory/` for memory templates
- **`CLAUDE.md`** — Starter project config (template for init-project command)
- **`SECURITY.md`** — Security policy (template for init-project command)
- **`.claude-plugin/plugin.json`** — Plugin manifest with name, version, description, author (object: `{"name": "..."}`, not a string)

### Marketplace (`/.claude-plugin/marketplace.json`)

Root-level marketplace catalog that references `./plugins/swishbot` as the single plugin.

## Skills

Each skill lives in `plugins/swishbot/skills/<skill-name>/` with a mandatory `SKILL.md` containing YAML frontmatter and methodology content. Optional subdirectories: `workflows/`, `examples/`, `scripts/`, `references/`.

Recognized Claude Code frontmatter fields: `name`, `description`, `user-invocable`, `disable-model-invocation`, `allowed-tools`, `argument-hint`, `model`, `context`, `agent`, `hooks`. Only use these in the `---` block — custom fields are ignored by Claude Code.

Skills with workflows use SKILL.md as a **router** that maps user intents to specific workflow files in the markdown body (not frontmatter). Each workflow is a focused, step-by-step procedure in `workflows/<workflow-name>.md`. Skills without workflows continue to work as flat methodology guides.

The `description` field is extracted via regex (`description:\s*"?([^"\n]+)"?`) — keep it on one line. Write descriptions as implicit triggers: include natural-language phrases users would say when they need this skill.

Hook scripts in skills must use `${CLAUDE_PLUGIN_ROOT}` paths, not `~/.claude/` paths.

## Agents

Each agent is a flat markdown file at `plugins/swishbot/agents/<agent-name>.md` containing YAML frontmatter and persona content. Agents compose multiple skills into a role — they tell Claude "you are a [role], use these skills."

Recognized Claude Code agent frontmatter fields: `name`, `description`, `model`, `color`, `tools`, `disallowedTools`, `skills`, `mcpServers`, `memory`, `permissionMode`, `maxTurns`, `hooks`. The fields currently used by swishbot agents:
- `skills` — injects full skill content at startup; subagents do NOT inherit parent skills, so this is essential
- `mcpServers` — references already-configured MCP servers by name (e.g., `dbt`); makes them available inside the agent
- `memory` — `project` scope gives each agent a persistent `.claude/agent-memory/<name>/` directory for cross-session learning
- `disallowedTools` — used on business-analyst to block `Bash`; keeps the agent focused on spec authoring

The skills an agent uses are also documented in a `## Skills` table in the body for human readers.

## Commands (Slash Commands)

Each command is a markdown file in `plugins/swishbot/commands/` with YAML frontmatter (`name`, `description`, `allowed-tools`) and instructions for Claude to follow. Commands replace the old CLI subcommands:

| Command | Replaces |
|---------|----------|
| `scaffold.md` | `swishbot scaffold` |
| `init-project.md` | `swishbot init-project` |
| `init-memory.md` | `swishbot init-memory` |

## Conventions

- Copyright header on all source files: `# Copyright (c) 2026 Swish BI Limited. All rights reserved.`
- Skills use kebab-case directories
- Ruff config: line-length 120, rules E/F/I/UP
- Tests validate plugin structure — skills, agents, commands, hooks, templates all present with correct frontmatter
- All hook scripts must use `${CLAUDE_PLUGIN_ROOT}` for paths
- Plugin version in `plugin.json` must be bumped for each release (cache invalidation)

## Hooks

All hooks are declared in a single file: `plugins/swishbot/hooks/hooks.json`. Do **not** duplicate hook declarations in individual `SKILL.md` frontmatter — that causes double-firing.

Claude Code matchers only support tool names (`Bash`, `Write|Edit`), not file-path or CWD patterns. Any directory/project scoping must happen **inside the hook script**.

Convention for `type: command` hooks:

- Read `tool_input.command` (not top-level `command`) and `cwd` from the JSON payload on stdin
- Short-circuit (exit 0) when CWD is outside the relevant project context. Existing scope markers:
  - `validate-sql.sh` fires only when `dbt_project.yml` is found in CWD or any ancestor (up to 8 levels)
  - `validate-terraform.sh` fires only when a `*.tf` file or `.terraform/` directory is found in CWD or any ancestor
  - Either script also fires when a `.swishbot-enforce` opt-in marker exists in CWD or an ancestor (escape hatch for non-standard project layouts)
- Use `set -euo pipefail` and bound any upward `dirname` walk with a depth limit (the existing scripts use 8)

Avoid `type: prompt` hooks. They spawn an LLM round-trip on every matched tool call, can't be conditionally scoped, and their natural-language responses get treated as blocking errors when the file isn't relevant (e.g., a markdown plan file evaluated against SQL conventions). Teach conventions through skill body content and `references/` files instead.

## New Skill Checklist

When adding a new skill, complete every step:

1. Create the skill directory in `plugins/swishbot/skills/<skill-name>/`
2. Write `SKILL.md` with YAML frontmatter (`name`, `description`, optional `argument-hint`) and methodology content
   - `description` must be a single line (extracted via regex); include natural-language trigger phrases
   - End file with copyright footer: `*Copyright (c) 2026 Swish BI Limited. All rights reserved.*`
   - For skills with workflows: add a routing table in the markdown body (not frontmatter) that maps intents to workflow files
3. Add optional subdirectories if needed: `workflows/`, `examples/`, `scripts/`
4. Add cross-references to related skills in a `## Related Skills` section
5. Update related skills to cross-reference back to the new skill
6. If the skill has hooks: add them to `plugins/swishbot/hooks/hooks.json` using `${CLAUDE_PLUGIN_ROOT}` paths, and scope the hook script by CWD/project marker (see the **Hooks** section above). Do not declare hooks in `SKILL.md` frontmatter.
7. Update the status table in `README.md` — add the skill row and set status to `:white_check_mark:`
8. Update the `CATEGORIES` dict in `docs/hooks/skills_catalog.py` — add the skill to the correct category
9. Run `uv run ruff check tests/ docs/` and `uv run ruff format tests/ docs/`
10. Run `uv run pytest -v` — all tests must pass
11. Bump `version` in `plugins/swishbot/.claude-plugin/plugin.json`

## Commit Checklist

- Lint and format pass (`uv run ruff check` + `uv run ruff format`)
- Tests pass (`uv run pytest -v`)
- If skills changed: update status tables in `README.md`, and `CATEGORIES` in `docs/hooks/skills_catalog.py`
- New skills need correct `name`/`description` frontmatter in SKILL.md
- If hooks changed: update `plugins/swishbot/hooks/hooks.json`
- Version bumped in `plugin.json` if releasing

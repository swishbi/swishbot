# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

swishbot is a Python CLI that distributes "skills" and "agents" into `~/.claude/` for Claude Code to reference during data engineering work. Skills are opinionated methodology guides; agents are persona definitions that compose multiple skills into roles (e.g., analytics-engineer, data-engineer).

## Commands

```bash
# Install dev environment (uses uv for package management)
uv sync --extra test

# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Run all tests
uv run pytest -v

# Run a single test
uv run pytest -v tests/test_cli.py::test_function_name

# Pre-commit hooks (ruff on commit, pytest on push)
uv run pre-commit install && uv run pre-commit install --hook-type pre-push
```

## Architecture

Single-module CLI (`src/swishbot/cli.py`) with seven subcommands routed via `match` statement:

- **`list`** — Discovers skills and agents by scanning `*/SKILL.md` and `*/AGENT.md`, extracts metadata from YAML frontmatter via regex
- **`install`** — Copies skill directories to `~/.claude/skills/` (or `--path`). With `--agent`, copies agent directories to `~/.claude/agents/`
- **`init`** — Scaffolds a new skill directory with `workflows/` subdir from `SKILL_TEMPLATE`
- **`init-project`** — Copies `src/swishbot/.claude/CLAUDE.md` and `SECURITY.md` into a target project's root
- **`hooks`** — Reads installed skills at a given path and prints a merged `hooks:` block from all SKILL.md frontmatter, suitable for pasting into `settings.json`
- **`init-memory`** — Creates `.claude/memory/` with shared project memory templates (`MEMORY.md`, `conventions.md`, `modeling-decisions.md`, `source-catalog.md`) and writes `.claude/settings.json` with a `Stop` hook that prompts Claude to update memory files after each session
- **`scaffold`** — Full project scaffold: copies all skills and agents, project template files (from `scaffold_templates/`), CLAUDE.md, SECURITY.md, and calls `_scaffold_memory()` to set up shared memory. Produces a complete `ingestion/` + `transformation/` + `orchestration/` project layout

Key constants: `CLAUDE_DIR`, `SKILLS_DIR`, `AGENTS_DIR`, `DEFAULT_INSTALL_PATH`, `DEFAULT_AGENT_INSTALL_PATH`, `CLAUDE_MD` (all `pathlib.Path`).

The source tree under `src/swishbot/.claude/` mirrors the install target `~/.claude/`:
- `src/swishbot/.claude/skills/` → `~/.claude/skills/`
- `src/swishbot/.claude/agents/` → `~/.claude/agents/`

## Skills

Each skill lives in `src/swishbot/.claude/skills/<skill-name>/` with a mandatory `SKILL.md` containing YAML frontmatter and methodology content. Optional subdirectories: `workflows/`, `examples/`, `scripts/`.

Recognized Claude Code frontmatter fields: `name`, `description`, `user-invocable`, `disable-model-invocation`, `allowed-tools`, `argument-hint`, `model`, `context`, `agent`, `hooks`. Only use these in the `---` block — custom fields are ignored by Claude Code.

Skills with workflows use SKILL.md as a **router** that maps user intents to specific workflow files in the markdown body (not frontmatter). Each workflow is a focused, step-by-step procedure in `workflows/<workflow-name>.md`. Skills without workflows continue to work as flat methodology guides.

The `description` field is extracted via regex (`description:\s*"?([^"\n]+)"?`) — keep it on one line. Write descriptions as implicit triggers: include natural-language phrases users would say when they need this skill.

## Agents

Each agent is a flat markdown file at `src/swishbot/.claude/agents/<agent-name>.md` containing YAML frontmatter (`name`, `description`, `model`, `color`, `skills`) and persona content. Agents compose multiple skills into a role — they tell Claude "you are a [role], use these skills."

Recognized Claude Code agent frontmatter fields: `name`, `description`, `model`, `color`, `tools`, `disallowedTools`, `skills`, `mcpServers`, `memory`, `permissionMode`, `maxTurns`, `hooks`. The fields currently used by swishbot agents:
- `skills` — injects full skill content at startup; subagents do NOT inherit parent skills, so this is essential
- `mcpServers` — references already-configured MCP servers by name (e.g., `dbt`); makes them available inside the agent even if the parent conversation has a different MCP context
- `memory` — `project` scope gives each agent a persistent `.claude/agent-memory/<name>/` directory for cross-session learning; auto-loads `MEMORY.md` into the system prompt
- `disallowedTools` — used on business-analyst to block `Bash`; keeps the agent focused on spec authoring, not command execution
The skills an agent uses are also documented in a `## Skills` table in the body for human readers.

Agents are authored by swishbot maintainers (no `init` scaffold). The `description` field follows the same regex extraction as skills.

## Conventions

- Python 3.10+ required (uses `match` statements)
- No runtime dependencies — stdlib only
- Copyright header on all source files: `# Copyright (c) 2026 Swish BI Limited. All rights reserved.`
- CLI commands follow `cmd_*` naming; skills use kebab-case directories
- Ruff config: line-length 120, rules E/F/I/UP
- Tests use monkeypatching and `tmp_path` for isolation; organized by command with section comments

## New Skill Checklist

When adding a new skill, complete every step:

1. Scaffold the skill directory: `swishbot init <skill-name>` (creates `SKILL.md` + `workflows/`)
2. Write `SKILL.md` with YAML frontmatter (`name`, `description`, optional `argument-hint`) and methodology content
   - `description` must be a single line (extracted via regex); include natural-language trigger phrases
   - End file with copyright footer: `*Copyright (c) 2026 Swish BI Limited. All rights reserved.*`
   - For skills with workflows: add a routing table in the markdown body (not frontmatter) that maps intents to workflow files
3. Add optional subdirectories if needed: `examples/`, `scripts/`
   - Add workflow files in `workflows/` if the skill has multi-step procedures
4. Add cross-references to related skills in a `## Related Skills` section
5. Update related skills to cross-reference back to the new skill
6. Update the status table in `README.md` — add the skill row and set status to `:white_check_mark:`
7. Update the status table in `src/swishbot/.claude/CLAUDE.md` — same as above
8. Update the `CATEGORIES` dict in `docs/hooks/skills_catalog.py` — add the skill to the correct category
9. Update the project structure tree in `README.md` if the directory layout changed
10. Run `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/`
11. Run `uv run pytest -v` — all tests must pass

## Commit Checklist

- Lint and format pass (`uv run ruff check` + `uv run ruff format`)
- Tests pass (`uv run pytest -v`)
- If skills changed: update status tables in both `README.md` and `src/swishbot/.claude/CLAUDE.md`, and `CATEGORIES` in `docs/hooks/skills_catalog.py`
- New skills need correct `name`/`description` frontmatter in SKILL.md

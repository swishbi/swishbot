# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

swishbot is a Python CLI that distributes "skills" — opinionated methodology guides in Markdown — into `~/.claude/skills/` for Claude Code to reference during data engineering work. Skills encode *how you think* about each layer of the data stack, not platform specifics.

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

Single-module CLI (`src/swishbot/cli.py`) with four subcommands routed via `match` statement:

- **`list`** — Discovers skills by scanning `src/swishbot/.claude/skills/*/SKILL.md`, extracts metadata from YAML frontmatter via regex
- **`install`** — Copies skill directories (including `workflows/` subdirs) to `~/.claude/skills/` (or `--path`)
- **`init`** — Scaffolds a new skill directory with `workflows/` subdir from `SKILL_TEMPLATE`
- **`init-project`** — Copies `src/swishbot/CLAUDE.md` (the user-facing template) into a target project

Key constants: `CLAUDE_DIR`, `SKILLS_DIR`, `DEFAULT_INSTALL_PATH`, `CLAUDE_MD` (all `pathlib.Path`).

The source tree under `src/swishbot/.claude/` mirrors the install target `~/.claude/`:
- `src/swishbot/.claude/skills/` → `~/.claude/skills/`
- `src/swishbot/.claude/agents/` → `~/.claude/agents/` (future)

## Skills

Each skill lives in `src/swishbot/.claude/skills/<skill-name>/` with a mandatory `SKILL.md` containing YAML frontmatter (`name`, `description`, optional `workflows`) and methodology content. Optional subdirectories: `workflows/`, `examples/`, `scripts/`.

Skills with workflows use SKILL.md as a **router** that maps user intents to specific workflow files. Each workflow is a focused, step-by-step procedure in `workflows/<workflow-name>.md`. Skills without workflows continue to work as flat methodology guides.

The `description` field is extracted via regex (`description:\s*"?([^"\n]+)"?`) — keep it on one line.

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
2. Write `SKILL.md` with YAML frontmatter (`name`, `description`, optional `workflows`) and methodology content
   - `description` must be a single line (extracted via regex)
   - End file with copyright footer: `*Copyright (c) 2026 Swish BI Limited. All rights reserved.*`
   - For skills with workflows: add `workflows` list to frontmatter and use SKILL.md as a router
3. Add optional subdirectories if needed: `examples/`, `scripts/`
   - Add workflow files in `workflows/` if the skill has multi-step procedures
4. Add cross-references to related skills in a `## Related Skills` section
5. Update related skills to cross-reference back to the new skill
6. Update the status table in `README.md` — add the skill row and set status to `:white_check_mark:`
7. Update the status table in `src/swishbot/CLAUDE.md` — same as above
8. Update the `CATEGORIES` dict in `docs/hooks/skills_catalog.py` — add the skill to the correct category
9. Update the project structure tree in `README.md` if the directory layout changed
10. Run `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/`
11. Run `uv run pytest -v` — all tests must pass

## Commit Checklist

- Lint and format pass (`uv run ruff check` + `uv run ruff format`)
- Tests pass (`uv run pytest -v`)
- If skills changed: update status tables in both `README.md` and `src/swishbot/CLAUDE.md`, and `CATEGORIES` in `docs/hooks/skills_catalog.py`
- New skills need correct `name`/`description` frontmatter in SKILL.md

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

swishbot is a Python CLI that distributes "skills" — opinionated methodology guides in Markdown — into `~/.claude/skills/` for Claude Code to reference during data engineering work. Skills encode *how you think* about each layer of the data stack, not platform specifics.

## Commands

```bash
# Install in dev mode
pip install -e ".[test]"

# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Run all tests
pytest -v

# Run a single test
pytest -v tests/test_cli.py::test_function_name

# Pre-commit hooks (ruff on commit, pytest on push)
pre-commit install && pre-commit install --hook-type pre-push
```

## Architecture

Single-module CLI (`src/swishbot/cli.py`) with four subcommands routed via `match` statement:

- **`list`** — Discovers skills by scanning `src/swishbot/skills/*/SKILL.md`, extracts metadata from YAML frontmatter via regex
- **`install`** — Copies skill directories to `~/.claude/skills/` (or `--path`)
- **`init`** — Scaffolds a new skill directory from `SKILL_TEMPLATE`
- **`init-project`** — Copies `src/swishbot/CLAUDE.md` (the user-facing template) into a target project

Key constants: `SKILLS_DIR`, `DEFAULT_INSTALL_PATH`, `CLAUDE_MD` (all `pathlib.Path`).

## Skills

Each skill lives in `src/swishbot/skills/<skill-name>/` with a mandatory `SKILL.md` containing YAML frontmatter (`name`, `description`) and methodology content. Optional subdirectories: `examples/`, `scripts/`.

The `description` field is extracted via regex (`description:\s*"?([^"\n]+)"?`) — keep it on one line.

## Conventions

- Python 3.10+ required (uses `match` statements)
- No runtime dependencies — stdlib only
- Copyright header on all source files: `# Copyright (c) 2026 Swish BI Limited. All rights reserved.`
- CLI commands follow `cmd_*` naming; skills use kebab-case directories
- Ruff config: line-length 120, rules E/F/I/UP
- Tests use monkeypatching and `tmp_path` for isolation; organized by command with section comments

## Commit Checklist

- Lint and format pass (`ruff check` + `ruff format`)
- Tests pass (`pytest -v`)
- If skills changed: update status tables in both `README.md` and `src/swishbot/CLAUDE.md`
- New skills need correct `name`/`description` frontmatter in SKILL.md

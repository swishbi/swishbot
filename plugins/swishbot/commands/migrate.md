---
name: migrate
description: "Migrate an existing dlt + dbt project into the swishbot structure with Dagster orchestration. Use when you have an existing data project that needs restructuring."
argument-hint: "<project-directory>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# Migrate an Existing Project

You are migrating an existing data project (dlt pipelines, dbt project, or both) into the swishbot project structure with Dagster orchestration.

## Phase 1: Discovery

1. **Parse the project directory** from `$ARGUMENTS`. If no directory is provided, default to the current working directory. Confirm with the user using AskUserQuestion.

2. **Detect dlt pipelines** — search the project for:
   - Python files containing `@dlt.source`, `@dlt.resource`, `dlt.pipeline(`
   - `.dlt/` configuration directories
   - Record every pipeline file and config directory found.

3. **Detect dbt project** — search for:
   - `dbt_project.yml` (the dbt project root)
   - Record the dbt project directory and all subdirectories (models, seeds, macros, tests, etc.)

4. **Check for existing Dagster** — look for `dagster_cloud.yaml`, `definitions.py`. If Dagster is already present, note it and ask the user whether to overwrite or skip orchestration setup.

5. **Check for existing project config** — look for `pyproject.toml`, `.claude/`, `.mcp.json`, `.env`, `.gitignore`.

6. **Present a migration summary** to the user listing:
   - dlt pipelines found (file paths)
   - dbt project found (directory path)
   - Existing Dagster detected (yes/no)
   - Existing config files detected
   - Proposed directory restructuring plan

   Ask the user to confirm before proceeding.

## Phase 2: Restructure

7. **Check if this is a git repo** by running `git rev-parse --is-inside-work-tree`. Use `git mv` for file moves if it is; use regular moves otherwise.

8. **Create target directories** (if they don't already exist):
   - `ingestion/`
   - `transformation/`
   - `orchestration/`
   - `tests/`

9. **Move dlt pipelines → `ingestion/`**:
   - Move all detected dlt pipeline Python files into `ingestion/`
   - Move `.dlt/` config directories alongside the pipeline code into `ingestion/.dlt/`
   - Warn the user about any credentials in `.dlt/secrets.toml` — these should NOT be committed

10. **Move dbt project → `transformation/`**:
    - Move the entire dbt project directory contents into `transformation/`
    - Preserve all subdirectories: `models/`, `seeds/`, `macros/`, `tests/`, `snapshots/`, `analyses/`
    - Preserve `dbt_project.yml`, `profiles.yml` (if present), `packages.yml` (if present)
    - Warn about `profiles.yml` — it may need path updates

## Phase 3: Add Dagster Orchestration

11. **Copy orchestration templates** from `${CLAUDE_PLUGIN_ROOT}/templates/orchestration/` into `orchestration/`:
    - `definitions.py` — single entry point
    - Component directories and files under `defs/`
    - Utility files under `utils/`
    - `__init__.py` files for all packages

12. **Create placeholder `defs.yaml`** files with TODO comments for each detected dlt pipeline:
    - Create `orchestration/defs/ingestion/dlt/defs.yaml` with a commented-out component entry per pipeline
    - Include instructions for wiring up each source

13. **Copy `dagster_cloud.yaml`** from `${CLAUDE_PLUGIN_ROOT}/templates/dagster_cloud.yaml` to the project root (skip if user chose to keep existing Dagster config).

## Phase 4: Add Project Config

14. **Merge `pyproject.toml`**:
    - If `pyproject.toml` exists, add missing dependencies without overwriting existing ones. Required deps: `dagster`, `dagster-webserver`, `dagster-dbt`, `dagster-dlt`, `dlt`, `dbt-core`
    - If it doesn't exist, copy from `${CLAUDE_PLUGIN_ROOT}/templates/pyproject.toml` and apply variable substitution

15. **Add `.env.example`** from `${CLAUDE_PLUGIN_ROOT}/templates/env.example`:
    - If `.env` already exists, do NOT overwrite it
    - If `.env.example` already exists, merge missing entries

16. **Append missing entries to `.gitignore`**:
    - If `.gitignore` exists, append any missing standard entries (`.env`, `__pycache__/`, `.dagster/`, `target/`, `dbt_packages/`, etc.)
    - If it doesn't exist, copy from `${CLAUDE_PLUGIN_ROOT}/templates/gitignore`

17. **Set up `.claude/` directory**:
    - Copy `CLAUDE.md` from `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` into `.claude/`
    - Copy `SECURITY.md` from `${CLAUDE_PLUGIN_ROOT}/SECURITY.md` into `.claude/`
    - Create `.claude/memory/` and copy memory templates from `${CLAUDE_PLUGIN_ROOT}/templates/memory/`
    - Create `.claude/settings.json` with plugin marketplace config:
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

18. **Merge `.mcp.json`**:
    - If `.mcp.json` exists, add any missing MCP server entries from `${CLAUDE_PLUGIN_ROOT}/templates/mcp.json` without overwriting existing ones
    - If it doesn't exist, copy from template

19. **Add `.devcontainer/` and `.github/workflows/`** from `${CLAUDE_PLUGIN_ROOT}/templates/` if not already present. Skip if they exist.

## Phase 5: Summary

20. **Print a summary** of everything that was done:

```
Migration complete: ./project-directory/

  Restructured:
    - dlt pipelines → ingestion/
    - dbt project  → transformation/
    - Dagster orchestration added → orchestration/

  Config added:
    - .claude/ (CLAUDE.md, SECURITY.md, memory templates, settings.json)
    - .mcp.json (MCP server configuration)
    - .env.example, .gitignore (merged)
    - pyproject.toml (dependencies merged)
    - dagster_cloud.yaml

  TODO checklist:
    □ Wire up dlt sources in orchestration/defs/ingestion/dlt/defs.yaml
    □ Verify dbt profile paths work from new transformation/ location
    □ Set up .env credentials (copy from .env.example)
    □ Review ingestion/.dlt/ for any hardcoded paths
    □ Run: uv sync && dagster dev
    □ Run: cd transformation && dbt debug
```

## Key Principles

- **Confirm before moving** — always show the plan and ask before any file moves
- **Merge, don't overwrite** — for pyproject.toml, .gitignore, .mcp.json, never clobber existing config
- **Use `git mv`** when in a git repo to preserve file history
- **Best-effort Dagster wiring** — create placeholder TODOs rather than broken configs
- **Don't rewrite dlt internals** — move files but don't change pipeline code
- **Warn about credentials** — flag .dlt/secrets.toml, .env, profiles.yml for manual review

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

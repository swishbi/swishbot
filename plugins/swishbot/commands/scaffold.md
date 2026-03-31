---
name: scaffold
description: "Scaffold a complete analytics project with ingestion, transformation, and orchestration layers. Creates a full dlt + dbt + Dagster project with Claude Code skills, agents, memory templates, and MCP configuration."
argument-hint: "<project-name>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - AskUserQuestion
---

# Scaffold a New Analytics Project

You are scaffolding a new analytics project. The project name is provided as `$ARGUMENTS`.

## Instructions

1. **Parse the project name** from `$ARGUMENTS`. If no name is provided, ask the user for one using AskUserQuestion.

2. **Derive variables:**
   - `project_name` = the argument as-is (kebab-case, e.g., `my-client`)
   - `project_name_snake` = replace hyphens and spaces with underscores, lowercase (e.g., `my_client`)

3. **Check if the target directory already exists.** If `./project_name/` exists, ask the user if they want to overwrite it.

4. **Copy all template files** from `${CLAUDE_PLUGIN_ROOT}/templates/` into the project directory, applying these transforms:
   - Replace `{project_name}` with the actual project name in all file contents
   - Replace `{project_name_snake}` with the snake_case version in all file contents
   - Apply these file renames:
     - `gitignore` → `.gitignore`
     - `env.example` → `.env.example`
     - `mcp.json` → `.mcp.json`
   - Apply these directory renames:
     - `devcontainer/` → `.devcontainer/`
     - `github/` → `.github/`
   - Skip the `memory/` subdirectory (handled separately in step 8)
   - Skip `settings.json` (merged into `.claude/settings.json` in step 8)

5. **Create `__init__.py` files** (empty) in these directories:
   - `ingestion/`
   - `orchestration/`
   - `orchestration/defs/`
   - `orchestration/defs/ingestion/`
   - `orchestration/defs/ingestion/dlt/`
   - `orchestration/defs/reporting/`
   - `orchestration/defs/reporting/powerbi/`
   - `orchestration/defs/transformation/`
   - `orchestration/defs/transformation/dbt/`
   - `orchestration/utils/`
   - `tests/`

6. **Create empty directories with `.gitkeep`** files:
   - `transformation/models/staging/`
   - `transformation/models/intermediate/`
   - `transformation/models/marts/`
   - `transformation/seeds/`
   - `transformation/macros/`
   - `transformation/tests/`

7. **Copy CLAUDE.md and SECURITY.md** from `${CLAUDE_PLUGIN_ROOT}/` into the project's `.claude/` directory.

8. **Set up shared project memory:**
   - Create `.claude/memory/` directory
   - Copy all files from `${CLAUDE_PLUGIN_ROOT}/templates/memory/` into `.claude/memory/`
   - Create `.claude/settings.json` with the following content:
   ```json
   {
     "permissions": {
       "allow": [
         "mcp__dbt__*",
         "mcp__dagster-dg-cli__*",
         "mcp__dlt__*",
         "mcp__powerbi-modeling__*",
         "mcp__powerbi-remote__*"
       ]
     },
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

9. **Print a summary** showing what was created:
   ```
   Scaffolded project: ./project_name/
     - ingestion/           dlt pipelines
     - transformation/      dbt project
     - orchestration/       Dagster orchestration
     - .claude/             Skills, agents, memory, project config

   Next steps:
     cd project_name
     uv sync
     dagster dev
   ```

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

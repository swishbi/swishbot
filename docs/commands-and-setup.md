# Commands & Setup

## Plugin installation

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

Both paths result in the same outcome: the plugin is installed and all skills, agents, hooks, and MCP servers auto-load into your Claude Code sessions.

## Slash commands

### `/swishbot:scaffold`

Scaffold a complete analytics project with ingestion, transformation, orchestration, and CI/CD.

```bash
/swishbot:scaffold my-client
```

| Argument | Description |
|----------|-------------|
| `name` | Project name (kebab-case) |

#### What gets created {#scaffold}

```
my-client/
  ingestion/              # dlt pipelines
  transformation/         # dbt project (models, seeds, macros, tests)
  orchestration/          # Dagster orchestration with dlt/dbt/Power BI components
  tests/                  # Project tests
  .claude/                # CLAUDE.md, SECURITY.md
  .devcontainer/          # VS Code Dev Container for local development
  .github/workflows/      # Dagster Cloud deployment workflows (disabled by default)
  pyproject.toml          # Project config with all dependencies
  dagster_cloud.yaml      # Dagster Cloud location config
```

The project name is substituted throughout — `pyproject.toml`, `dbt_project.yml`, `dagster_cloud.yaml`, deployment workflows, and the Dev Container config all use the name you provide.

#### Dev Container

The scaffolded project includes a `.devcontainer/` directory for VS Code Dev Containers. Open the project in VS Code and select **Reopen in Container** to get a fully configured development environment with Python, uv, Dagster, dbt, and dlt ready to go.

Pre-installed VS Code extensions: Claude Code, Python, Pylance, Ruff, YAML, dbt Power User, Better Jinja, TMDL.

#### Dagster Cloud deployments

The `.github/workflows/` directory includes two GitHub Actions workflows for Dagster Cloud:

- **`deploy.yml`** — Deploys to production on push to `main`
- **`branch_deployments.yml`** — Creates branch deployments on pull requests

Both workflows are **disabled by default**. They will skip until you enable them:

1. Set up your [Dagster Cloud](https://dagster.io/cloud) organization
2. Add the following GitHub repository secrets: `DAGSTER_CLOUD_API_TOKEN`, `ORGANIZATION_ID`
3. Add a GitHub repository variable: `DAGSTER_CLOUD_ENABLED` = `true`

The `DAGSTER_CLOUD_URL` in each workflow is set to `http://<project-name>.dagster.plus` — update this if your Dagster Cloud organization name differs from the project name.

### `/swishbot:init-project`

Create a starter `CLAUDE.md` and `SECURITY.md` in your project directory.

```bash
/swishbot:init-project
```

Both files are created together — `CLAUDE.md` defines project conventions and skill references, while `SECURITY.md` provides security guidelines for SQL safety, credential handling, and prompt injection defense.

### `/swishbot:init-memory`

Scaffold a project memory directory with templates for Claude to persist decisions across sessions.

```bash
/swishbot:init-memory
```

This creates a `.claude/memory/` directory with template files and a `Stop` hook that prompts Claude to save decisions at the end of each session:

- `MEMORY.md`
- `conventions.md`
- `modeling-decisions.md`
- `source-catalog.md`

## Hooks

Hooks are Claude Code event handlers (`PreToolUse`, `PostToolUse`, `Stop`) that enforce rules automatically. When the plugin is installed, all hooks are active — no manual setup required.

Current hooks:

| Skill | Event | Matcher | Script |
|-------|-------|---------|--------|
| `dba-security` | PreToolUse | `Write\|Edit` | `validate-sql.sh` |
| `dlt` | PreToolUse | `Write\|Edit` | `check-secrets.sh` |
| `iac-terraform` | PreToolUse | `Write\|Edit` | `validate-terraform.sh` |

Hook scripts use `${CLAUDE_PLUGIN_ROOT}` paths to locate scripts within the plugin directory.

## MCP servers

MCP servers are auto-configured via the plugin's `.mcp.json`. No manual setup needed. Available servers:

| Server | Description |
|--------|-------------|
| `dbt` | dbt project introspection and MetricFlow queries |
| `dagster` | Dagster asset and job management |
| `dlt` | dlt pipeline and source inspection |
| `powerbi` | Power BI semantic model and report management |

## Memory architecture

`/swishbot:init-memory` sets up **shared project memory** — a single `.claude/memory/` directory that all agents contribute to and read from. This fills a gap that native Claude Code memory mechanisms don't cover:

| Memory type | Path | Scope | Managed by |
|-------------|------|-------|------------|
| Per-agent memory | `.claude/agent-memory/<agent-name>/` | Single agent | Auto-managed by Claude Code (`memory: project`) |
| Shared project memory | `.claude/memory/` | All agents + main session | Updated via Stop hook |

**Per-agent memory** is declared with `memory: project` in each agent's frontmatter. Claude Code automatically creates `.claude/agent-memory/<agent-name>/MEMORY.md` and injects it into the agent's system prompt at startup — no configuration needed. Use this for agent-specific learnings.

**Shared project memory** is what `/swishbot:init-memory` creates. All agents read it at session start, and the Stop hook prompts Claude to write cross-agent decisions (naming conventions, modeling choices, source quirks) back to it.

To also load shared memory in the **main session** (not inside an agent), add an `@` import to your `CLAUDE.md`:

```markdown
@.claude/memory/MEMORY.md
```

The project `CLAUDE.md` template (from `/swishbot:init-project`) includes a commented-out version of this import — uncomment it after running `/swishbot:init-memory`.

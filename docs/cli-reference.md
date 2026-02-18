# CLI Reference

All commands are run via the `swishbot` CLI.

## `swishbot list`

List all available skills and agents with their descriptions.

```bash
swishbot list
```

Example output:

```
Available skills:

  dba-security            DBA security practices
  dbt-intermediate        Building the intermediate/silver layer
  dbt-marts               Building the mart/gold layer
  dbt-staging             Building the staging/bronze layer
  ...

Install with: swishbot install <skill-name>

Available agents:

  analytics-engineer  Builds dbt models across all layers with MCP tooling
  business-analyst    Guides stakeholders from idea to implementation-ready spec
  data-engineer       Builds ingestion pipelines with proper security
  data-modeler        Designs and builds dimensional models across the full dbt DAG
  platform-engineer   Sets up infrastructure, security, and platform architecture

Install agent: swishbot install --agent <agent-name>
```

## `swishbot install`

Install one or more skills or agents to your Claude environment.

```bash
# Single skill
swishbot install dbt-staging

# Multiple skills
swishbot install dbt-staging dbt-intermediate dbt-marts

# All skills
swishbot install --all

# Custom install path
swishbot install dbt-staging --path ~/my-project/.claude/skills

# Install an agent
swishbot install --agent data-modeler

# Install all agents
swishbot install --agent --all
```

| Option | Description |
|--------|-------------|
| `skills` | One or more skill or agent names to install |
| `--all` | Install all available skills (or all agents with `--agent`) |
| `--agent` | Install agents instead of skills (default target: `~/.claude/agents/`) |
| `--path` | Custom install directory (default: `~/.claude/skills/` or `~/.claude/agents/`) |

If a skill or agent is already installed, it will be overwritten.

## `swishbot scaffold`

Scaffold a complete analytics project with ingestion, transformation, orchestration, and CI/CD.

```bash
# Scaffold in current directory
swishbot scaffold my-client

# Scaffold in a specific directory
swishbot scaffold my-client --path ~/projects

# Overwrite existing project
swishbot scaffold my-client --force
```

| Option | Description |
|--------|-------------|
| `name` | Project name (kebab-case) |
| `--path` | Parent directory (default: current directory) |
| `--force` | Overwrite an existing directory |

### What gets created

```
my-client/
  ingestion/              # dlt pipelines
  transformation/         # dbt project (models, seeds, macros, tests)
  orchestration/          # Dagster orchestration with dlt/dbt/Power BI components
  tests/                  # Project tests
  .claude/                # Skills, agents, CLAUDE.md, SECURITY.md
  .devcontainer/          # VS Code Dev Container for local development
  .github/workflows/      # Dagster Cloud deployment workflows (disabled by default)
  pyproject.toml          # Project config with all dependencies
  dagster_cloud.yaml      # Dagster Cloud location config
```

The project name is substituted throughout — `pyproject.toml`, `dbt_project.yml`, `dagster_cloud.yaml`, deployment workflows, and the Dev Container config all use the name you provide.

### Dev Container

The scaffolded project includes a `.devcontainer/` directory for VS Code Dev Containers. Open the project in VS Code and select **Reopen in Container** to get a fully configured development environment with Python, uv, Dagster, dbt, and dlt ready to go.

Pre-installed VS Code extensions: Claude Code, Python, Pylance, Ruff, YAML, dbt Power User, Better Jinja, TMDL.

### Dagster Cloud deployments

The `.github/workflows/` directory includes two GitHub Actions workflows for Dagster Cloud:

- **`deploy.yml`** — Deploys to production on push to `main`
- **`branch_deployments.yml`** — Creates branch deployments on pull requests

Both workflows are **disabled by default**. They will skip until you enable them:

1. Set up your [Dagster Cloud](https://dagster.io/cloud) organization
2. Add the following GitHub repository secrets: `DAGSTER_CLOUD_API_TOKEN`, `ORGANIZATION_ID`
3. Add a GitHub repository variable: `DAGSTER_CLOUD_ENABLED` = `true`

The `DAGSTER_CLOUD_URL` in each workflow is set to `http://<project-name>.dagster.plus` — update this if your Dagster Cloud organization name differs from the project name.

## `swishbot init-project`

Create a starter `CLAUDE.md` and `SECURITY.md` in your project directory.

```bash
# Current directory
swishbot init-project

# Specific directory
swishbot init-project --path ~/my-project

# Overwrite existing
swishbot init-project --force
```

| Option | Description |
|--------|-------------|
| `--path` | Target directory (default: current directory) |
| `--force` | Overwrite an existing `CLAUDE.md` |

Both files are copied together — `CLAUDE.md` defines project conventions and installed skills, while `SECURITY.md` provides security guidelines for SQL safety, credential handling, and prompt injection defense.

## `swishbot init`

Scaffold a new skill with a template `SKILL.md`.

```bash
swishbot init my-new-skill
```

This creates a new skill directory under the bundled skills folder with a template ready to fill in. See [Creating Skills](creating-skills.md) for details.

## `swishbot hooks`

List hooks provided by installed skills. Hooks are Claude Code event handlers (e.g., `PreToolUse`, `PostToolUse`) that skills define to enforce rules automatically.

```bash
# Default install path
swishbot hooks

# Custom install path
swishbot hooks --path ~/my-project/.claude/skills
```

| Option | Description |
|--------|-------------|
| `--path` | Skills install path (default: `~/.claude/skills/`) |

Example output:

```
Installed hooks:

  dba-security  PreToolUse  (Write|Edit)  validate-sql.sh
  dbt-staging   PreToolUse  (Write|Edit)  check-staging-refs.sh
  dbt-style     PreToolUse  (Write|Edit)  check-style.sh
```

## `swishbot init-memory`

Scaffold a project memory directory with templates for Claude to persist decisions across sessions.

```bash
# Current directory
swishbot init-memory

# Specific directory
swishbot init-memory --path ~/my-project

# Overwrite existing
swishbot init-memory --force
```

| Option | Description |
|--------|-------------|
| `--path` | Target directory (default: current directory) |
| `--force` | Overwrite an existing memory directory |

Example output:

```
  ✓ .claude/settings.json (session capture hook)

  ✓ Memory templates → ~/my-project/.claude/memory
    - MEMORY.md
    - conventions.md
    - modeling-decisions.md
    - source-catalog.md

Claude will update these files as decisions are made during sessions.
```

This creates a `.claude/memory/` directory with template files and a `settings.json` with a `Stop` hook that prompts Claude to save decisions at the end of each session.

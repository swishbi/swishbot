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

  analytics-architecture  Analytics reference architecture
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

## `swishbot init-project`

Create a starter `CLAUDE.md` in your project directory.

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

## `swishbot init`

Scaffold a new skill with a template `SKILL.md`.

```bash
swishbot init my-new-skill
```

This creates a new skill directory under the bundled skills folder with a template ready to fill in. See [Creating Skills](creating-skills.md) for details.

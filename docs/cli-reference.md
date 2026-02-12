# CLI Reference

All commands are run via the `swishbot` CLI.

## `swishbot list`

List all available skills with their descriptions.

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
```

## `swishbot install`

Install one or more skills to your Claude environment.

```bash
# Single skill
swishbot install dbt-staging

# Multiple skills
swishbot install dbt-staging dbt-intermediate dbt-marts

# All skills
swishbot install --all

# Custom install path
swishbot install dbt-staging --path ~/my-project/.claude/skills
```

| Option | Description |
|--------|-------------|
| `skills` | One or more skill names to install |
| `--all` | Install all available skills |
| `--path` | Custom install directory (default: `~/.claude/skills/`) |

If a skill is already installed, it will be overwritten.

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

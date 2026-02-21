# Getting Started

## Installation

```bash
pip install swishbot
```

Or install from source in dev mode:

```bash
git clone https://github.com/swishbi/swishbot.git
cd swishbot
pip install -e .
```

## Install skills

Browse what's available:

```bash
swishbot list
```

Install the skills you need:

```bash
# Install a single skill
swishbot install dbt

# Install multiple skills
swishbot install dbt dimensional-modeling

# Install everything
swishbot install --all

# Install to a custom path
swishbot install dbt --path ~/my-project/.claude/skills
```

Skills are copied to `~/.claude/skills/` by default.

## Install agents

Agents compose multiple skills into a focused persona. Install one to give Claude a specific role:

```bash
# Install a single agent
swishbot install --agent analytics-engineer

# Install all agents
swishbot install --agent --all

# Install to a custom path
swishbot install --agent analytics-engineer --path ~/my-project/.claude/agents
```

Agents are copied to `~/.claude/agents/` by default.

## Set up your project

Generate a starter `CLAUDE.md` in your project directory:

```bash
cd ~/my-project
swishbot init-project
```

This creates a `CLAUDE.md` file that:

- Lists your installed skills
- Defines project conventions
- Describes your project structure and platform environment

Edit the file to uncomment the skills you've installed and fill in your project details. Claude reads this file to understand your project context and apply the right skill guidance.

!!! tip
    If you already have a `CLAUDE.md`, use `--force` to overwrite it:

    ```bash
    swishbot init-project --force
    ```

## Set up hooks

Some skills include hooks that automatically enforce rules (e.g., SQL validation, style checks). See what hooks your installed skills provide:

```bash
swishbot hooks
```

Copy the hook definitions into your `.claude/settings.json` to activate them. See the [CLI Reference](cli-reference.md#swishbot-hooks) for details.

## Set up project memory (optional)

Scaffold a memory directory so Claude can persist modeling decisions, source metadata, and conventions across sessions:

```bash
swishbot init-memory
```

This creates `.claude/memory/` with template files and a session-end hook. See the [CLI Reference](cli-reference.md#swishbot-init-memory) for details.

## Verify it works

Open Claude Code in your project and start working. Claude will automatically read the `CLAUDE.md` and apply the methodology from your installed skills.

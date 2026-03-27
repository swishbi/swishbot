# Creating Skills

## Create a new skill

Create a new skill directory under `plugins/swishbot/skills/`:

```bash
mkdir plugins/swishbot/skills/my-new-skill
```

Add a `SKILL.md` file with YAML frontmatter and methodology content.

!!! tip
    The `skill-creator` skill can help you create and iterate on new skills. Ask Claude to "create a new skill" and it will guide you through the process.

## Skill anatomy

Every skill has at minimum a `SKILL.md` with this structure:

```markdown
---
name: skill-name
description: "When to use this skill and what it does."
---

# Skill Title

## Overview
What this skill does and the methodology behind it.

## Methodology
Your opinionated approach — the reasoning and patterns
that make Claude work the way you would.

## Patterns
Concrete patterns with examples. Show what good output looks like.

## Anti-Patterns
What to avoid — the mistakes you've seen that Claude
should steer away from.

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*
```

### Frontmatter

The YAML frontmatter at the top is required:

- **`name`** — the skill directory name (kebab-case)
- **`description`** — a short description of when to use this skill. Keep it on one line (extracted via regex). Write it as an implicit trigger: include natural-language phrases users would say when they need this skill.

Optional frontmatter fields recognized by Claude Code:

- **`argument-hint`** — hint text shown to users (e.g., `"[source-name]"`)
- **`hooks`** — Claude Code event handlers (`PreToolUse`, `PostToolUse`, `Stop`) that enforce rules automatically. See [Hooks](#hooks) below.
- **`user-invocable`**, **`disable-model-invocation`**, **`allowed-tools`**, **`model`**, **`context`**, **`agent`** — additional Claude Code skill fields

### Optional additions

Skills can include extra directories:

- **`references/`** — examples, templates, lookup tables that the skill references
- **`scripts/`** — helper scripts the skill can invoke (often referenced by hooks)
- **`workflows/`** — step-by-step procedures for multi-step tasks, routed from the SKILL.md body
- **`examples/`** — example files and patterns

### Workflow routing

Skills with multiple workflows use SKILL.md as a **router** that maps user intents to specific workflow files. Add a routing table in the markdown body (not frontmatter) that maps intents to workflow files in `workflows/<workflow-name>.md`. Each workflow is a focused, step-by-step procedure.

## Writing methodology

Skills encode *how to think about problems*, not platform-specific implementation details. Focus on:

- **What** to do and **why** — Claude already knows the platforms
- **Patterns** — concrete examples of good output
- **Anti-patterns** — common mistakes to avoid (often the most valuable part)

The goal is to make Claude work the way you would, applying your experience and opinions consistently.

## Hooks

Skills can define hooks in their frontmatter to enforce rules automatically. Hooks fire on Claude Code events like `PreToolUse` (before a tool runs) or `PostToolUse` (after). A hook can be a `command` (runs a script) or a `prompt` (asks Claude to verify something).

Example frontmatter with a hook:

```yaml
---
name: my-skill
description: "Example skill with a pre-tool hook."
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/skills/my-skill/scripts/validate.sh"
          timeout: 10
---
```

Place hook scripts in `scripts/` inside the skill directory. Hook scripts must use `${CLAUDE_PLUGIN_ROOT}` paths — this ensures they work correctly when installed as a plugin.

When the plugin is installed, hooks from all skills are merged into `plugins/swishbot/hooks/hooks.json` and auto-loaded. No manual hook configuration needed.

## Testing a skill

During development, test your skill by running Claude Code against a real scenario in the plugin repo. Iterate on the `SKILL.md` until Claude produces correct output on the first shot.

## New skill checklist

When adding a new skill, complete every step:

1. Create the skill directory in `plugins/swishbot/skills/<skill-name>/`
2. Write `SKILL.md` with YAML frontmatter (`name`, `description`, optional `argument-hint`) and methodology content
    - `description` must be a single line (extracted via regex); include natural-language trigger phrases
    - End file with copyright footer: `*Copyright (c) 2026 Swish BI Limited. All rights reserved.*`
    - For skills with workflows: add a routing table in the markdown body that maps intents to workflow files
3. Add optional subdirectories if needed: `workflows/`, `examples/`, `scripts/`
4. Add cross-references to related skills in a `## Related Skills` section
5. Update related skills to cross-reference back to the new skill
6. If the skill has hooks: add them to `plugins/swishbot/hooks/hooks.json` using `${CLAUDE_PLUGIN_ROOT}` paths
7. Update the status table in `README.md` — add the skill row and set status to `:white_check_mark:`
8. Update the `CATEGORIES` dict in `docs/hooks/skills_catalog.py` — add the skill to the correct category
9. Run `uv run ruff check tests/ docs/` and `uv run ruff format tests/ docs/`
10. Run `uv run pytest -v` — all tests must pass
11. Bump `version` in `plugins/swishbot/.claude-plugin/plugin.json`

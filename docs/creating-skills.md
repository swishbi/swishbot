# Creating Skills

## Scaffold a new skill

```bash
swishbot init my-new-skill
```

This creates a new skill directory with a template `SKILL.md` ready to fill in.

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
```

### Frontmatter

The YAML frontmatter at the top is required:

- **`name`** — the skill directory name (kebab-case)
- **`description`** — a short description of when to use this skill. This is displayed in `swishbot list` and in the docs

Optional frontmatter fields recognized by Claude Code:

- **`argument-hint`** — hint text shown to users (e.g., `"[source-name]"`)
- **`hooks`** — Claude Code event handlers (`PreToolUse`, `PostToolUse`, `Stop`) that enforce rules automatically. See [Hooks](#hooks) below.
- **`user-invocable`**, **`disable-model-invocation`**, **`allowed-tools`**, **`model`**, **`context`**, **`agent`** — additional Claude Code skill fields

### Optional additions

Skills can include extra directories:

- **`references/`** — examples, templates, lookup tables that the skill references
- **`scripts/`** — helper scripts the skill can invoke (often referenced by hooks)
- **`workflows/`** — step-by-step procedures for multi-step tasks, routed from the SKILL.md body

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
name: dbt-style
description: "Cross-cutting dbt style conventions"
hooks:
  PreToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "~/.claude/skills/dbt-style/scripts/check-style.sh"
          timeout: 10
---
```

Place hook scripts in `scripts/` inside the skill directory. Use `swishbot hooks` to list all hooks across installed skills.

## Testing a skill

Point Claude Code at the skill and run it against a real scenario. Iterate on the `SKILL.md` until Claude produces correct output on the first shot.

```bash
# Install your skill locally
swishbot install my-new-skill

# Open Claude Code in a test project and verify
# the methodology is applied correctly
```

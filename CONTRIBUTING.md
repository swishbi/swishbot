# Contributing to swishbot

## Setup

```bash
# Clone and install in dev mode with test dependencies
git clone https://github.com/swishbi/swishbot.git
cd swishbot
pip install -e ".[test]"
```

## Running tests

```bash
pytest -v
```

## Linting & formatting

```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

CI runs these automatically on push and PR to `main` across Python 3.10-3.13.

## Creating a new skill

```bash
swishbot init my-new-skill
```

This scaffolds a new skill directory with a SKILL.md template.

### Skill anatomy

Every skill has at minimum a `SKILL.md` with this structure:

```markdown
---
name: skill-name
description: "When to use this skill and what it does."
---

# Skill Title

## Overview
What this skill does and the methodology behind it.

## [Your methodology sections]
The opinionated guidance that makes Claude work like you.
```

Optional additions:
- `references/` — examples, templates, lookup tables
- `scripts/` — helper scripts the skill can invoke

### Testing a skill

Point Claude Code at the skill and run it against a real scenario. Iterate on the SKILL.md until Claude produces correct output on the first shot.

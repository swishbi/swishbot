# Contributing to swishbot

## Setup

1. Clone the repo and move into it:

   ```bash
   git clone https://github.com/swishbi/swishbot.git
   cd swishbot
   ```

2. Install the project in dev mode with test dependencies:

   ```bash
   pip install -e ".[test]"
   ```

3. Set up the pre-commit hooks (these automatically check your code before each commit):

   ```bash
   pre-commit install
   pre-commit install --hook-type pre-push
   ```

   > New to pre-commit? See the [pre-commit docs](https://pre-commit.com/).

## Running checks

Run these from the project root before committing:

```bash
# Lint — checks for code issues
ruff check src/ tests/

# Format — auto-fixes formatting
ruff format src/ tests/

# Tests
pytest -v
```

If you installed the pre-commit hooks above, lint and format run automatically on every commit, and tests run before every push. CI also runs all three on every PR.

> New to ruff? See the [ruff docs](https://docs.astral.sh/ruff/).

## Commit checklist

Before committing, make sure you've covered everything:

- [ ] **Lint & format** — `ruff check src/ tests/` and `ruff format src/ tests/` pass cleanly
- [ ] **Tests pass** — `pytest -v` with no failures
- [ ] **Version bump** — update `version` in `pyproject.toml` if this is a release-worthy change
- [ ] **Skill tables updated** — if you added, removed, or changed a skill's availability, update the status tables in both `README.md` and `src/swishbot/CLAUDE.md`
- [ ] **SKILL.md frontmatter** — new or renamed skills have correct `name` and `description` in their frontmatter
- [ ] **Project structure** — if you added new files/directories, update the tree in `README.md`

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

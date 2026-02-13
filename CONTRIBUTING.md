# Contributing to swishbot

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for package management and development tooling.

1. Clone the repo and move into it:

   ```bash
   git clone https://github.com/swishbi/swishbot.git
   cd swishbot
   ```

2. Install `uv` if you don't have it:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Install the project with test dependencies:

   ```bash
   uv sync --extra test
   ```

4. Set up the pre-commit hooks (these automatically check your code before each commit):

   ```bash
   uv run pre-commit install
   uv run pre-commit install --hook-type pre-push
   ```

   > New to pre-commit? See the [pre-commit docs](https://pre-commit.com/).

## Running checks

Run these from the project root before committing:

```bash
# Lint — checks for code issues
uv run ruff check src/ tests/

# Format — auto-fixes formatting
uv run ruff format src/ tests/

# Tests
uv run pytest -v
```

If you installed the pre-commit hooks above, lint and format run automatically on every commit, and tests run before every push. CI also runs all three on every PR.

> New to ruff? See the [ruff docs](https://docs.astral.sh/ruff/).

## Commit checklist

Before committing, make sure you've covered everything:

- [ ] **Lint & format** — `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/` pass cleanly
- [ ] **Tests pass** — `uv run pytest -v` with no failures
- [ ] **Version bump** — update `version` in `pyproject.toml` if this is a release-worthy change
- [ ] **Skill tables updated** — if you added, removed, or changed a skill's availability, update the status tables in both `README.md` and `src/swishbot/CLAUDE.md`, and the `CATEGORIES` dict in `docs/hooks/skills_catalog.py`
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

## Related Skills
- **[other-skill](../other-skill/SKILL.md)** — Brief description of the relationship

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*
```

Optional additions:
- `examples/` — example files, templates, reference implementations
- `scripts/` — helper scripts the skill can invoke

### New skill checklist

Complete every step when adding a skill:

- [ ] **Scaffold** — `swishbot init <skill-name>`
- [ ] **Write SKILL.md** — YAML frontmatter (`name`, `description` on one line) + methodology content
- [ ] **Copyright footer** — `*Copyright (c) 2026 Swish BI Limited. All rights reserved.*`
- [ ] **Add examples** — `examples/` and/or `scripts/` subdirectories if applicable
- [ ] **Cross-reference** — add a `## Related Skills` section linking to related skills
- [ ] **Back-reference** — update related skills to link back to the new skill
- [ ] **README.md status table** — add the skill row with `:white_check_mark:` status
- [ ] **src/swishbot/CLAUDE.md status table** — same as above
- [ ] **Docs catalog hook** — add skill to the correct category in `docs/hooks/skills_catalog.py`
- [ ] **README.md project tree** — update if directory layout changed
- [ ] **Lint & format** — `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/`
- [ ] **Tests pass** — `uv run pytest -v`

### Testing a skill

Point Claude Code at the skill and run it against a real scenario. Iterate on the SKILL.md until Claude produces correct output on the first shot.

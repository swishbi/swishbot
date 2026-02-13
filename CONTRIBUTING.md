# Contributing to swishbot

There are two ways to contribute: **writing skills** (Markdown content — no programming required) and **developing the CLI** (Python code). Pick the section that fits.

---

## Contributing Skills (no programming required)

Skills are Markdown files that teach Claude how to think about a specific part of the data stack. If you can write a clear methodology doc, you can contribute a skill.

### Prerequisites

You need three things installed on your machine:

1. **Git** — version control, used to download the project and submit changes.
   - **Mac:** Open Terminal and run `xcode-select --install`. This installs Git along with other developer tools.
   - **Windows:** Open PowerShell and run `winget install --id Git.Git -e`. This installs Git and gives you "Git Bash," a terminal you will use for all commands below.
   - **Linux (Ubuntu/Debian):** Open a terminal and run `sudo apt update && sudo apt install git`.
   - **Linux (Fedora):** Open a terminal and run `sudo dnf install git`.
   - To verify it worked, open a terminal and run `git --version`. You should see a version number.

2. **VS Code** — a free text editor. You will use this to view and edit files, and to run Claude Code.
   - **Mac:** Download from [code.visualstudio.com](https://code.visualstudio.com/).
   - **Windows:** Open PowerShell and run `winget install --id Microsoft.VisualStudioCode -e`.
   - **Linux:** Download from [code.visualstudio.com](https://code.visualstudio.com/) or install via your package manager.

3. **Claude Code** — the AI assistant that can help you write skills and complete the checklist. Install it one of two ways:
   - **VS Code extension (recommended):** Open VS Code, go to the Extensions tab (the square icon on the left sidebar), search for "Claude Code," and click Install.
   - **Command line:** Open a terminal and run `npm install -g @anthropic-ai/claude-code`. This requires [Node.js](https://nodejs.org/) — download the LTS version if you do not have it (Windows: `winget install --id OpenJS.NodeJS.LTS -e`).
   - Either way, you will need an Anthropic API key or a Claude subscription to use it.

### First-time setup

Open a terminal (Mac: Terminal app; Windows: Git Bash; Linux: your terminal of choice) and run these commands one at a time:

```bash
# 1. Download the project to your computer
git clone https://github.com/swishbi/swishbot.git

# 2. Move into the project folder
cd swishbot

# 3. Create a branch for your work (replace "my-new-skill" with the skill name)
git checkout -b feat/my-new-skill
```

You now have the project on your machine and are on your own branch, which keeps your changes separate until they are reviewed.

### Writing a new skill

You can create a skill **manually** or **with Claude Code**. Either way, the same checklist must be completed before submitting.

#### Option A: Use Claude Code (recommended)

If you have Claude Code installed, open a terminal in the project folder and start a session:

```bash
claude
```

Then describe what you want to build. For example:

> "Create a new skill called data-quality-testing. It should teach Claude how to think about writing data quality tests for a dbt project."

Claude Code will read the project's `CLAUDE.md` file, which contains the **New Skill Checklist** — the definitive list of everything that must be done when adding a skill. Claude Code will follow that checklist automatically: scaffolding the directory, writing the SKILL.md, updating the status tables, adding cross-references, and running lint/tests.

Review what Claude Code produces before committing. You own the methodology content — Claude Code handles the mechanical steps.

#### Option B: Create the skill manually

If you prefer to do it by hand, follow the **New Skill Checklist** in `CLAUDE.md` (in the project root). Here is a summary of what it requires:

1. **Create the skill folder** at `src/swishbot/skills/your-skill-name/`. Skill names use kebab-case (lowercase, hyphens between words).

2. **Write `SKILL.md`** inside that folder using this template:

   ```markdown
   ---
   name: your-skill-name
   description: "A single sentence explaining when to use this skill and what it does."
   ---

   # Skill Title

   ## Overview

   Who is the intended persona (e.g., "You are acting as a business analyst")?
   What does this skill help Claude do? When should it be used?

   ## Methodology

   ### 1. First Step
   What to do and how to think about it.

   ### 2. Second Step
   Continue with the methodology...

   ## Anti-Patterns
   - Common mistakes to avoid and why they are mistakes.

   ## Related Skills
   - **[other-skill](../other-skill/SKILL.md)** — Brief description of how it relates

   ---

   *Copyright (c) 2026 Swish BI Limited. All rights reserved.*
   ```

   **Important details:**
   - The `description` field must be a **single line** (no line breaks). It appears in the skill catalog.
   - The `name` field must match the folder name exactly.
   - Always include the copyright footer at the bottom.

3. **Update the skill tables** — three files need a new row for your skill (alphabetical order within the category):
   - `README.md` — status table and project structure tree
   - `src/swishbot/CLAUDE.md` — status table
   - `docs/hooks/skills_catalog.py` — `CATEGORIES` dictionary

4. **Add cross-references** — link to related skills in your `## Related Skills` section, and update those related skills to link back to yours.

> The full checklist with exact details is in `CLAUDE.md` at the project root. When in doubt, refer to that file — it is the source of truth.

#### Submit your changes

```bash
# See what you changed
git status

# Stage all your changes
git add -A

# Commit with a short description of what you did
git commit -m "feat: add your-skill-name skill"

# Push your branch to GitHub
git push -u origin feat/my-new-skill
```

After pushing, GitHub will show you a link to create a **pull request** (PR). Open that link in your browser and click "Create pull request." This submits your changes for review — nothing goes live until it is approved.

> **Note:** CI (automated checks) will run on your pull request. If something fails, don't worry — ask for help in the PR comments.

### Updating an existing skill

1. Make sure you are on a new branch: `git checkout -b fix/skill-name-update`
2. Edit the `SKILL.md` file directly — or open Claude Code and describe the change you want to make
3. If you changed the `description` field, update it in `README.md` and `src/swishbot/CLAUDE.md` too
4. Commit and push using the same steps from "Submit your changes" above

---

## Developing the CLI (Python)

This section covers working on the `swishbot` Python CLI itself.

### Prerequisites

- **Python 3.10+** — [download here](https://www.python.org/downloads/)
- **Git** — see the Git installation instructions above
- **uv** — a fast Python package manager. Install it:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

  > uv replaces pip, virtualenv, and pip-tools. It manages the project's Python dependencies and virtual environment automatically. [uv docs](https://docs.astral.sh/uv/)

### Setup

```bash
# Clone and enter the project
git clone https://github.com/swishbi/swishbot.git
cd swishbot

# Install the project with test dependencies
uv sync --extra test

# Set up pre-commit hooks (auto-checks code on every commit/push)
uv run pre-commit install
uv run pre-commit install --hook-type pre-push
```

> **What are pre-commit hooks?** They automatically run lint and format checks when you commit, and tests when you push. This catches problems before they reach CI. [pre-commit docs](https://pre-commit.com/)

### Running checks

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

> **What is ruff?** A fast Python linter and formatter that enforces consistent code style. [ruff docs](https://docs.astral.sh/ruff/)

### Commit checklist

Before committing, make sure you've covered everything:

- [ ] **Lint & format** — `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/` pass cleanly
- [ ] **Tests pass** — `uv run pytest -v` with no failures
- [ ] **Version bump** — update `version` in `pyproject.toml` if this is a release-worthy change
- [ ] **Skill tables updated** — if you added, removed, or changed a skill's availability, update the status tables in both `README.md` and `src/swishbot/CLAUDE.md`, and the `CATEGORIES` dict in `docs/hooks/skills_catalog.py`
- [ ] **SKILL.md frontmatter** — new or renamed skills have correct `name` and `description` in their frontmatter
- [ ] **Project structure** — if you added new files/directories, update the tree in `README.md`

---

## Skill anatomy reference

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

## Testing a skill

Point Claude Code at the skill and run it against a real scenario. Iterate on the SKILL.md until Claude produces correct output on the first shot.

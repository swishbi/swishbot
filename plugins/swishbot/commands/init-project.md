---
name: init-project
description: "Install a starter CLAUDE.md and SECURITY.md into your project's .claude/ directory. Use when setting up a new project for Claude Code with swishbot conventions."
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

# Initialize Project Configuration

You are setting up a project with swishbot's starter CLAUDE.md and SECURITY.md.

## Instructions

1. **Determine the target directory.** Default is `./.claude/` in the current working directory. Create the directory if it doesn't exist.

2. **Check for existing files.** If `.claude/CLAUDE.md` already exists, ask the user if they want to overwrite it using AskUserQuestion.

3. **Copy CLAUDE.md** from `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` to `.claude/CLAUDE.md`. Read the source file first, then write it to the target.

4. **Copy SECURITY.md** from `${CLAUDE_PLUGIN_ROOT}/SECURITY.md` to `.claude/SECURITY.md`. Read the source file first, then write it to the target.

5. **Copy settings.json** from `${CLAUDE_PLUGIN_ROOT}/.claude/settings.json` to `.claude/settings.json`. Read the source file first, then write it to the target. If `.claude/settings.json` already exists, skip silently — do not overwrite user customizations.

6. **Print a summary:**
   ```
   Installed:
     CLAUDE.md    → .claude/CLAUDE.md
     SECURITY.md  → .claude/SECURITY.md
     settings.json → .claude/settings.json

   Edit the CLAUDE.md to uncomment your installed skills and fill in project details.
   ```

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

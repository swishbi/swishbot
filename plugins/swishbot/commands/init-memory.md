---
name: init-memory
description: "Scaffold shared project memory directory with cross-agent templates. Use when setting up project memory for Claude Code sessions to persist decisions across conversations."
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - AskUserQuestion
---

# Initialize Project Memory

You are setting up shared project memory templates for cross-agent knowledge persistence.

## Instructions

1. **Check if `.claude/memory/` already exists.** If it does, ask the user if they want to overwrite using AskUserQuestion.

2. **Create `.claude/memory/` directory** if it doesn't exist.

3. **Copy memory templates** from `${CLAUDE_PLUGIN_ROOT}/templates/memory/` into `.claude/memory/`:
   - `MEMORY.md` — Auto-loaded into system prompt; key decisions and active sources
   - `conventions.md` — Project-specific naming, SQL style, testing, materialization overrides
   - `modeling-decisions.md` — Dimensional modeling decision log
   - `source-catalog.md` — Source system catalog with loader and staging info

   Read each template file from the plugin, then write it to the target.

4. **Print a summary:**
   ```
   Memory templates → .claude/memory/
     - MEMORY.md
     - conventions.md
     - modeling-decisions.md
     - source-catalog.md

   Claude will update these files as decisions are made during sessions.
   ```

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

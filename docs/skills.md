# Skills Catalog

Skills are self-contained methodology guides that Claude reads to execute data engineering and analytics work. Each skill encodes opinionated, platform-agnostic guidance for a specific layer of the data stack.

All skills auto-load when the swishbot plugin is installed — no per-skill install step. Claude invokes skills automatically based on the task at hand, or you can reference a skill by name (e.g., "use the dbt skill").

Some skills include **hooks** — Claude Code event handlers that automatically enforce rules when Claude writes or edits files. For example, `dlt` validates for hardcoded credentials and `dba-security` checks for SQL permission patterns. Hooks are active as soon as the plugin is installed.

## Available Skills

<!-- SKILLS_CATALOG -->

# Skills Catalog

Skills are self-contained methodology guides that Claude reads to execute data engineering and analytics work. Each skill encodes opinionated, platform-agnostic guidance for a specific layer of the data stack.

Some skills include **hooks** — Claude Code event handlers that automatically enforce rules when Claude writes or edits files. For example, `dbt-style` validates SQL formatting and `dba-security` checks for credential patterns. Run `swishbot hooks` to see which hooks your installed skills provide.

Install any skill with:

```bash
swishbot install <skill-name>
```

## Available Skills

<!-- SKILLS_CATALOG -->

# Security Policy — swishbot contributors

This document covers security practices for contributing to the swishbot repository. For user-facing security guidance distributed to projects, see `src/swishbot/.claude/SECURITY.md`.

## Commit Checklist

Before every commit, verify:

- **No API keys or tokens** — search for `AKIA`, `sk-`, `ghp_`, `token=`, `password=`
- **No personal paths** — replace `/Users/yourname/` or `/home/yourname/` with generic paths
- **No `.env` files staged** — check `git status` for `.env`, `credentials.json`, or similar
- **No internal URLs** — company-internal dashboards, wikis, or API endpoints should not appear in skill content

## Skill Developer Guidance

When writing skills that interact with external systems:

1. **Never embed credentials in skill content** — use environment variable references (`$ENV_VAR`, `os.environ["KEY"]`, `dlt.secrets.value`)
2. **Hook scripts must be read-only** — hooks should validate and warn, never modify files or make network calls
3. **Validate all file paths in scripts** — hook scripts receive tool input as JSON; sanitize before using in shell commands
4. **Test hook scripts in isolation** — ensure they handle empty input, missing fields, and malformed JSON gracefully
5. **Document security implications** — if a skill's methodology involves running SQL or API calls, note the risks in the skill content

## Reporting Vulnerabilities

If you discover a security vulnerability in swishbot or any distributed skill, please email security@swishbi.com rather than opening a public issue.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

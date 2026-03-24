---
name: tech-docs
description: "Use when writing technical documentation for data platform work — setup guides, runbooks, data dictionaries, pipeline READMEs, architecture notes, troubleshooting guides, or multi-document reference suites."
---

# Technical Documentation Skill

Write clear, beginner-friendly technical documentation that is accessible to newcomers while remaining technically accurate.

## Documentation Style Characteristics

### Target Audience
- Engineers new to the specific technology being documented
- Operators who need step-by-step procedures under pressure (runbooks)
- Stakeholders who need to understand what the data platform does and why

### Writing Principles
1. **Clarity over brevity** — Be explicit rather than assuming knowledge
2. **Progressive complexity** — Start simple, add complexity as needed
3. **Action-oriented** — Focus on what users need to do, not just what things are
4. **Validation steps** — Include ways to verify each step worked
5. **Safety warnings** — Flag potentially destructive or irreversible operations before the step
6. **Link, don't duplicate** — Link to official documentation for external tools rather than documenting them yourself

### Linking to Source Documentation

Avoid documenting external tools, services, or APIs that have their own official documentation. These change frequently and your documentation will become stale.

**Document yourself:**
- Your specific configuration choices and why you made them
- How external tools integrate with your specific setup
- Custom scripts, workflows, or configurations you've created
- Troubleshooting issues specific to your environment

**Link to instead:**
- How a tool or service works in general
- Installation instructions for external tools
- API reference documentation

**Example:**

```markdown
## CI/CD Pipeline

This project uses GitHub Actions for continuous integration.

> [!NOTE]
> For workflow syntax and available options, see the
> [GitHub Actions documentation](https://docs.github.com/en/actions).

### Our Workflow Configuration

We run tests on every pull request targeting `main`. Here's what our workflow does:
...
```

## Document Structure

### Required Sections

#### Overview
Brief introduction explaining:
- What the document covers
- Why someone would follow this guide
- Expected outcome

#### Prerequisites
List everything needed before starting:
- Software requirements and versions
- Required access or credentials
- Prior steps that must be completed

Use callout blocks for context:
```markdown
> [!NOTE]
> Brief informational callouts

> [!TIP]
> Helpful suggestions or best practices

> [!WARNING]
> Important cautions about data loss or breaking changes

> [!IMPORTANT]
> Critical information that must not be missed
```

#### Step-by-Step Instructions
- Number major steps sequentially
- Use command blocks with syntax highlighting
- Explain what each command does AFTER showing it
- Include expected output when relevant
- Add verification steps after significant changes

#### Verification/Testing
How to confirm the setup works:
- Test commands to run
- Expected results
- What success looks like

### Optional Sections

#### Troubleshooting
Common issues organized by:
- **Symptoms**: What the user observes
- **Solutions**: Step-by-step fixes, ordered from most to least likely

#### Next Steps
- Related documentation to explore
- Links to advanced topics

## Code Block Formatting

Always specify the language for syntax highlighting:

```markdown
\`\`\`bash
uv run python ingestion/pipeline.py
\`\`\`
```

Explain commands immediately after showing them:

```markdown
\`\`\`bash
dlt pipeline my_pipeline run
\`\`\`

This command executes the pipeline, extracting data from the source and loading it into the destination.
```

For long commands, use backslash continuation and explain each parameter:

```markdown
\`\`\`bash
docker run -d \
  --name container-name \
  -p 8080:80 \
  -v /local/path:/container/path \
  image-name
\`\`\`

Parameters:
- `-d`: Run in detached mode
- `-p 8080:80`: Map host port 8080 to container port 80
- `-v`: Mount local directory into container
```

## Tone and Voice

- **Use active voice** — "Run the command" not "The command should be run"
- **Use imperative mood** — "Edit the configuration file" not "You should edit the configuration file"
- **Be direct but supportive** — "This step requires administrator privileges. If you get a permission error, add `sudo` before the command."
- **Explain the "why" when it matters** — "Restart the service to apply configuration changes" not just "Restart the service"

## Data Platform Documentation Patterns

Patterns specific to data engineering and analytics work.

### Pipeline README

Every ingestion pipeline should have a README that explains:

```markdown
# [Source Name] Pipeline

Ingests [data type] from [source system] into [destination].

## What it loads

| Resource | Destination table | Frequency | Notes |
|----------|------------------|-----------|-------|
| orders | raw.shopify_orders | Hourly | Full refresh |
| customers | raw.shopify_customers | Daily | Append |

## Prerequisites

- `SHOPIFY_API_KEY` set in `.dlt/secrets.toml`
- Destination warehouse connection configured in `config.toml`

## Running manually

\`\`\`bash
uv run python ingestion/shopify/pipeline.py
\`\`\`

## Schema notes

[Any quirks about the source schema, type coercions, or known data quality issues]
```

### Data Dictionary

Document business meaning that SQL column names alone cannot convey:

```markdown
## orders

**Grain:** One row per order. An order can have multiple line items (see `order_items`).

**Key columns:**

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | string | Shopify order ID. Globally unique. |
| `financial_status` | string | Payment state: `paid`, `pending`, `refunded`, `voided` |
| `fulfillment_status` | string | `null` means unfulfilled. `partial` means some items shipped. |
| `cancelled_at` | timestamp | Null if not cancelled. Populated even if later uncancelled. |

**Business rules:**
- Revenue recognition uses `financial_status = 'paid'` only
- Returns are modelled as negative `order_items` rows, not order deletions
```

### Architecture Decision Record (ADR)

Capture the why behind significant technical choices so future engineers understand context:

```markdown
# ADR-001: Use dlt for ingestion over Fivetran

**Date:** 2025-01-15
**Status:** Accepted

## Context

We needed to ingest data from 3 custom REST APIs that Fivetran doesn't support natively.

## Decision

Use dlt for all ingestion. Custom connector development is straightforward, pipelines
live in version control alongside dbt models, and there's no per-row cost.

## Consequences

- Engineers need Python skills to add new sources
- Schema evolution is handled automatically by dlt
- No GUI for non-technical stakeholders to monitor runs (use Dagster UI instead)
```

### Operational Runbook

Documentation for responding to incidents or performing routine operations:

```markdown
# Runbook: Pipeline Failure — [Pipeline Name]

**Severity:** [P1/P2/P3]
**On-call channel:** #data-oncall

## Symptoms

- Dagster asset `[asset_name]` shows failed status
- Downstream models haven't refreshed since [expected time]
- Alert fired in [monitoring tool]

## Diagnosis

1. Check the Dagster run log for the error message:
   ```
   [Dagster URL]/runs/[run-id]
   ```

2. Common errors and their causes:
   - `AuthenticationError` → API token expired, see [Secrets Management doc]
   - `SchemaChange` → Source added/removed columns, see [Schema Evolution doc]
   - `RateLimitError` → Source API throttled, pipeline will retry automatically

## Resolution

### Token expired
1. Rotate the token in [secret store]
2. Re-run the failed pipeline from Dagster UI

### Unexpected schema change
1. Review the diff in the dlt load table
2. If safe, re-run the pipeline (dlt will evolve the schema)
3. If breaking, open a PR to update the dlt resource definition

## Escalation

If unresolved after 30 minutes, escalate to [team lead] via [channel].
```

## Multi-Document Suite Organization

When creating comprehensive documentation (5+ related documents):

### Document Naming Convention
Use numeric prefixes for sequential documentation:
```
00-overview.md
01-setup.md
02-configuration.md
03-operations.md
04-troubleshooting.md
```

### Index Document
Create a master document that:
- Lists all documents in order
- Briefly describes what each covers
- Provides a "where to start" guide for different audiences

### Progressive Disclosure
Order documents from:
1. Essential setup (must read)
2. Core operations (should read)
3. Advanced topics (read as needed)
4. Reference material (search as needed)
5. Troubleshooting (use when problems arise)

### Consistent Structure Across Documents
- Same heading hierarchy
- Same callout style usage
- Similar section ordering
- Consistent terminology

## Common Documentation Patterns

### Installation Procedure

```markdown
## Installation

### Prerequisites
[List requirements]

### Install
\`\`\`bash
[installation command]
\`\`\`

### Verify
\`\`\`bash
[verification command]
\`\`\`

Expected output:
\`\`\`
[example output]
\`\`\`
```

### Troubleshooting Entry

```markdown
#### Service Won't Start

**Symptoms**: Error message when running command

**Solutions**:

1. Check if service is already running:
   \`\`\`bash
   sudo systemctl status service-name
   \`\`\`

2. Check logs for errors:
   \`\`\`bash
   sudo journalctl -u service-name
   \`\`\`
```

## Quality Checklist

Before finalizing documentation:

- [ ] All commands tested and verified
- [ ] Prerequisites clearly listed
- [ ] Code blocks have language specification
- [ ] Verification steps included
- [ ] Warnings for destructive or irreversible operations placed BEFORE the step
- [ ] Placeholders clearly marked (e.g., `YOUR_API_KEY`)
- [ ] Consistent terminology throughout
- [ ] Logical progression from simple to complex
- [ ] Each document has clear purpose stated at top
- [ ] External tools linked to official docs (not duplicated)
- [ ] See `references/setup-guide-template.md` for a copy-paste starting point

## Related Skills

- **swishbot:dbt** — dbt model YAML documentation (column descriptions, tests)
- **swishbot:dlt** — Pipeline structure and schema conventions to document
- **swishbot:dagster** — Asset descriptions and job metadata
- **swishbot:requirements-discovery** — Developer specifications that feed into technical docs

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

# Debug Pipeline

Diagnose and fix a failing dlt pipeline.

## Step 1: Inspect Pipeline State

Use the pipeline MCP server to inspect the schema and loaded data:

```bash
dlt pipeline <pipeline-name> mcp
```

Or use CLI tools directly:

```bash
dlt pipeline <pipeline-name> show
```

Check:
- Pipeline state and last run status
- Schema definition and any recent changes
- Loaded data counts and timestamps

## Step 2: Check Pipeline Traces

Review error details from the pipeline trace:
- Identify which resource or step failed
- Check for authentication errors, rate limits, or schema changes
- Look for partial loads that may need cleanup

## Step 3: Simplify and Isolate

Isolate the failing resource and test it independently:
- Comment out all resources except the failing one
- Run with a minimal configuration
- Add logging or print statements to narrow down the failure point
- Test with a small data sample before running the full extraction

## Step 4: Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Auth errors | Expired credentials or wrong scope | Check `.dlt/secrets.toml` and refresh tokens |
| Schema mismatch | Source API changed field types | Update pipeline schema or add column type hints |
| Rate limiting | Too many API calls | Add `max_table_nesting` or reduce parallelism |
| Partial load | Pipeline crashed mid-extraction | Run again — dlt is idempotent by default |
| Missing tables | Resource not yielding data | Check API filters, date ranges, or empty source |

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

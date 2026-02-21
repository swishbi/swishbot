# Debug Pipeline

Diagnose and fix a failing dlt pipeline.

## Step 1: Enable Verbose Logging

Before investigating, enable detailed logging to capture the full error context:

```bash
# Set log level to INFO for pipeline execution details
export RUNTIME__LOG_LEVEL=INFO

# Show full HTTP error response bodies (helpful for REST API pipelines)
export RUNTIME__REQUESTS__HTTP_SHOW_ERROR_BODY=true
```

Add these to your shell environment or `.env` file. For one-off debugging:

```bash
RUNTIME__LOG_LEVEL=INFO python my_pipeline.py
```

## Step 2: Inspect Pipeline State

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

## Step 3: Check Pipeline Traces

Review error details from the pipeline trace:
- Identify which resource or step failed
- Check for authentication errors, rate limits, or schema changes
- Look for partial loads that may need cleanup

## Step 4: Simplify and Isolate

Isolate the failing resource and test it independently:
- Comment out all resources except the failing one
- Run with a minimal configuration
- Add logging or print statements to narrow down the failure point
- Test with a small data sample before running the full extraction

## Step 5: Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Auth errors (401/403) | Expired credentials or wrong scope | Check `.dlt/secrets.toml` and refresh tokens |
| Schema mismatch | Source API changed field types | Update pipeline schema or add column type hints |
| Rate limiting (429) | Too many API calls | Add `max_table_nesting` or reduce parallelism |
| Partial load | Pipeline crashed mid-extraction | Run again — dlt is idempotent by default |
| Missing tables | Resource not yielding data | Check API filters, date ranges, or empty source |
| Custom paginator returning wrong page count | `update_state` not checking total correctly | Log `response.json()` in paginator; compare `total_count` vs `current_count` calculation |
| OAuth token expiry mid-run | Long-running pipeline outlasts token TTL | Implement token refresh in auth class; check `is_token_expired()` before each request |
| Column type mismatch between runs | Source added new fields or changed types | Add explicit `columns` hints to the resource; set `nullable: True` for optional fields |
| `DictValidationException` | Config field in wrong location (e.g. `columns` inside `endpoint` instead of resource) | Move the field to the correct level — `columns`, `primary_key`, `write_disposition` go on the resource, not inside `endpoint` |
| `InvalidStepFunctionType` | Processing step function has wrong signature | `map` takes and returns a dict; `filter` takes a dict and returns bool; `yield_map` takes a dict and yields dicts |
| Empty incremental loads | `initial_value` format doesn't match API expectations | Check that `initial_value` and `convert` function produce the format the API expects (ISO 8601, Unix timestamp, YYYY-MM-DD) |

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

# Refactor to Intermediate

Extract complex logic from an existing mart into an intermediate model.

## Step 1: Identify Candidates

Look for these signals in existing mart models:

- **4-5+ joins** in a single model — the SQL is hard to read and debug
- **Repeated CTE patterns** across multiple marts — the same join or aggregation appears in several places
- **Grain changes mid-model** — a CTE aggregates to a different grain before joining back
- **Complex business logic** — window functions, multi-condition CASE statements, or pivots that deserve their own tests

Use the dbt MCP `get_lineage` and `get_model_details` tools to understand the current DAG before refactoring.

## Step 2: Extract the Logic

1. **Identify the CTE(s)** in the mart that should become intermediate models
2. **Create the intermediate model** using the naming convention `int_<source>__<description>.sql` (or `int_<entity>_<description>.sql` in `conformed/` when it combines sources)
3. **Move the CTE logic** into the new intermediate model with a `select * from` final CTE
4. **Replace the CTE** in the mart with a `{{ ref('int_...') }}` import
5. **Set materialization** to ephemeral (or view if expensive and multiply-referenced)

## Step 3: Verify

1. Run `dbt build` on both the new intermediate model and the downstream mart
2. Compare row counts and sample data before and after to confirm the refactor is behavior-preserving
3. If the intermediate model is ephemeral, verify it does not appear in the warehouse schema
4. Check if other marts can now reference the intermediate model instead of duplicating the logic

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

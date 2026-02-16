# Create Incremental Mart

Convert a table-materialized mart to incremental when build times become excessive.

## Step 1: Confirm Incremental Is Needed

Move to incremental when:

- The mart's `table` materialization takes too long during scheduled builds
- The source data has a reliable timestamp or monotonically increasing key for filtering
- The cost of full refresh outweighs the complexity of incremental logic

Do NOT use incremental for:

- Small tables (< millions of rows) — the overhead is not worth it
- Tables without a reliable incremental key — you will end up with duplicates or missing data
- Early development — start with `table` and optimize later

## Step 2: Configure the Model

```sql
{{
    config(
        materialized='incremental',
        unique_key='event_id',
        incremental_strategy='merge'
    )
}}

with

events as (
    select * from {{ ref('stg_app__events') }}
    {% if is_incremental() %}
    where created_at > (select max(created_at) from {{ this }})
    {% endif %}
),

final as (
    select
        event_id,
        user_id,
        event_type,
        event_properties,
        created_at
    from events
)

select * from final
```

Key decisions:

- **`unique_key`** — the column(s) that uniquely identify a row. Used by the merge strategy to update existing rows.
- **`incremental_strategy`** — `merge` (upsert) is the safest default. Use `append` only for pure insert-only event streams.
- **`is_incremental()` filter** — only applies on incremental runs. Full refresh (`dbt run --full-refresh`) processes all data.

## Step 3: Validate

1. Run a full refresh first: `dbt run --full-refresh --select <model_name>`
2. Run an incremental build: `dbt run --select <model_name>`
3. Compare row counts — incremental should match or exceed (for late-arriving data) the full refresh count
4. Spot-check recent records to confirm the incremental filter is working correctly

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

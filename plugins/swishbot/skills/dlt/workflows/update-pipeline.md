# Update Pipeline

Modify an existing dlt pipeline — add endpoints, handle schema changes, change write dispositions, retire resources, or tune performance.

## Step 1: Add a New Resource

Add a new API endpoint or table to an existing pipeline.

### Set `initial_value` Deliberately

Every incremental resource needs an `initial_value` that matches the API's expected format. Get this wrong and the first load silently returns nothing:

```python
# REST API — ISO 8601 timestamp
"incremental": {
    "cursor_path": "modifiedDate",
    "initial_value": "2024-01-01T00:00:00Z",
}

# SQL database — date string matching the column type
@dlt.resource(write_disposition="merge", primary_key="id")
def new_table(
    updated_at=dlt.sources.incremental("updated_at", initial_value="2024-01-01"),
):
    ...
```

> **Tip:** Set `initial_value` to the earliest date you need, not "the beginning of time." A wide range means a slow first load and unnecessary data.

### Test in Isolation

Run only the new resource before adding it to the full pipeline:

```bash
python <pipeline_file>.py --resources <new_resource>
```

Check the loaded data with the MCP server or CLI before moving on. See [Debug Pipeline Step 5](debug-pipeline.md#step-5-common-testing--debugging-commands) for more testing commands.

### REST API Pattern

Add the new endpoint to the `resources` list in your REST API source config:

```python
"resources": [
    # ... existing resources ...
    {
        "name": "new_endpoint",
        "endpoint": {
            "path": "api/v1/new-endpoint",
            "params": {"modified_since": "{incremental.start_value}"},
        },
        "write_disposition": "merge",
        "primary_key": "id",
        "incremental": {
            "cursor_path": "modifiedDate",
            "initial_value": "2024-01-01T00:00:00Z",
        },
    },
]
```

See [Create REST API Pipeline](create-rest-api-pipeline.md) for full auth, pagination, and column typing details.

### SQL Database Pattern

Add a new resource function or table name to the source:

```python
@dlt.resource(write_disposition="merge", primary_key="id")
def new_table(
    updated_at=dlt.sources.incremental("updated_at", initial_value="2024-01-01"),
):
    query = f"""
        SELECT * FROM source_schema.new_table
        WHERE updated_at > '{updated_at.last_value}'
    """
    yield from db_client.execute(query)
```

See [Create SQL Database Pipeline](create-sql-database-pipeline.md) for connection setup and SQL-over-REST patterns.

## Step 2: Handle Schema Evolution

dlt handles most schema changes automatically. Understand what happens so you know when to intervene.

### Automatic Behavior (no action needed)

| Change | dlt Behavior |
|--------|-------------|
| New field in source data | Column added to destination automatically |
| Field removed from source | Existing column stays, new rows get `NULL` |
| Type widens (int → float) | Column type updated automatically |
| Type narrows or conflicts | **Variant column** created (e.g., `amount__v_text`) |

> **Tip:** Variant columns (suffixed `__v_<type>`) signal a type conflict. They keep data safe but create modeling headaches — fix the root cause rather than working around variants downstream.

### Lock Types with Column Hints

When you know a field's type and don't want dlt to guess, add explicit `columns` hints:

```python
"columns": {
    "amount": {"data_type": "decimal", "precision": 18, "scale": 2},
    "external_id": {"data_type": "text"},  # Prevent numeric inference on IDs
    "created_date": {"data_type": "timestamp"},
}
```

See [Create REST API Pipeline Step 6](create-rest-api-pipeline.md#step-6-set-column-types) for full column typing details.

### Enforce Strict Schema with `schema_contract`

When you want the pipeline to **fail** on unexpected schema changes instead of silently adapting:

```python
source = my_source()
source.schema_contract = {
    "tables": "evolve",       # Allow new tables
    "columns": "freeze",      # Reject new columns
    "data_type": "freeze",    # Reject type changes
}
```

Options per key: `"evolve"` (accept silently), `"discard_row"` (drop offending rows), `"discard_value"` (null out offending fields), `"freeze"` (raise exception).

### Breaking Changes: Drop and Reload

When a source makes a breaking change (renamed fields, restructured responses), the cleanest fix is:

```bash
# Drop the affected table and its state
dlt pipeline <pipeline-name> drop <table_name>

# Update your pipeline code to match the new schema, then reload
python <pipeline_file>.py --resources <resource_name>
```

## Step 3: Change Write Disposition or Primary Key

Changing `write_disposition` or `primary_key` on an existing resource requires a drop-and-reload — you cannot change these in-place.

### Decision Tree

```
What needs to change?
├── Switch replace → merge
│   └── Drop table → add primary_key + incremental → reload
├── Switch merge → replace
│   └── Drop table → remove primary_key + incremental → reload
└── Change primary_key columns
    └── Drop table → update primary_key → reload
```

### Procedure

1. **Drop the affected table:**

```bash
dlt pipeline <pipeline-name> drop <table_name>
```

2. **Update your pipeline code** — change `write_disposition` and/or `primary_key` in the resource definition.

3. **Reload from scratch:**

```bash
python <pipeline_file>.py --resources <resource_name>
```

> **Tip:** When switching from `replace` to `merge`, you must add a `primary_key` and typically an `incremental` cursor. Without a primary key, merge has nothing to match on.

## Step 4: Remove or Deprecate a Resource

### Drop Table and State

Remove the table from the destination and clear its pipeline state:

```bash
# Drop table and state
dlt pipeline <pipeline-name> drop <table_name>

# Drop only state (keep table data for reference)
dlt pipeline <pipeline-name> drop <table_name> --state-only
```

### Disable in Code

After dropping, remove or disable the resource so it doesn't reload on the next run:

**Python resources:** Delete the resource function or remove it from the `resources` list.

**SQL file resources:** Prefix the filename with `_` (e.g., `old_table.sql` → `_old_table.sql`) to exclude it from discovery.

### Verify Clean State

Confirm the resource is fully removed:

```bash
# Check pipeline state — resource should be gone
dlt pipeline <pipeline-name> show

# Run the pipeline — no trace of the old resource
python <pipeline_file>.py
```

See [Debug Pipeline Step 5](debug-pipeline.md#step-5-common-testing--debugging-commands) for state inspection commands.

## Step 5: Tune Performance

### Parallelize Parent Resources

Enable parallel extraction on independent top-level resources:

```python
@dlt.resource(parallelized=True)
def large_table(...):
    ...
```

> **Tip:** Only use `parallelized=True` on parent resources that don't depend on each other. Child resources (those using `resolve`) already run in the context of their parent.

### Control Table Nesting

Flatten deeply nested JSON to reduce table count and join complexity:

```python
pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination="snowflake",
    dataset_name="raw",
)

# Flatten everything — no child tables
source = my_source()
source.max_table_nesting = 0

# Or allow one level of nesting
source.max_table_nesting = 1
```

### Page and Batch Sizing

For REST APIs, tune page size to balance throughput and memory:

```python
"endpoint": {
    "path": "api/v1/records",
    "params": {
        "page_size": 500,  # Increase from default if API allows
    },
}
```

For database sources, use server-side cursors or chunked queries to control memory usage.

### Profile with Progress Logging

Enable progress logging to identify slow resources:

```python
pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination="snowflake",
    dataset_name="raw",
    progress="log",  # Logs extraction/load progress per resource
)
```

Watch for resources with disproportionately long extraction times — these are candidates for pagination tuning, parallelization, or incremental loading.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

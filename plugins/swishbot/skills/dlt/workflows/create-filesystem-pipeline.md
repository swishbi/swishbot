# Create Cloud File Storage Pipeline

Build a dlt pipeline that loads data from cloud storage (Azure Blob, S3, GCS) or local filesystem into a warehouse.

**Reference example:** `examples/filesystem_pipeline.py`

## Step 1: Configure Bucket Access

### Supported Storage

| Provider | Bucket URL | Credentials |
|----------|-----------|-------------|
| Azure Blob | `az://container-name` | `CREDENTIALS__AZURE_STORAGE_ACCOUNT_NAME`, `CREDENTIALS__AZURE_STORAGE_ACCOUNT_KEY` |
| AWS S3 | `s3://bucket-name` | `CREDENTIALS__AWS_ACCESS_KEY_ID`, `CREDENTIALS__AWS_SECRET_ACCESS_KEY` |
| Google Cloud Storage | `gs://bucket-name` | `CREDENTIALS__GCLOUD_SERVICE_ACCOUNT_JSON` (path to JSON key file) |
| Local filesystem | `/path/to/dir` or `file:///path` | None |

Install the relevant extra:

```bash
pip install "dlt[filesystem]"   # Core filesystem support
pip install "dlt[az]"           # Azure Blob Storage
pip install "dlt[s3]"           # AWS S3
pip install "dlt[gs]"           # Google Cloud Storage
```

### Credential Setup

dlt resolves credentials from multiple sources in this priority order: **environment variables > `secrets.toml` > vault providers > default arguments**. We prefer environment variables managed through a `.env` file.

Reference: https://dlthub.com/docs/general-usage/credentials/setup

Environment variable names use uppercase with double underscores (`__`) as section separators. Define them in a `.env` file at the project root:

```bash
# .env — loaded by your orchestrator, dotenv, or shell
# IMPORTANT: .env must be in .gitignore — never commit it

# Filesystem source credentials (for my_pipeline.py with source function arguments)
SOURCES__MY_PIPELINE__CREDENTIALS__AZURE_STORAGE_ACCOUNT_NAME="myaccount"
SOURCES__MY_PIPELINE__CREDENTIALS__AZURE_STORAGE_ACCOUNT_KEY="mykey"
SOURCES__MY_PIPELINE__BUCKET_URL="az://my-container"

# Destination credentials
DESTINATION__POSTGRES__CREDENTIALS__HOST="localhost"
DESTINATION__POSTGRES__CREDENTIALS__DATABASE="analytics"
DESTINATION__POSTGRES__CREDENTIALS__USER="loader"
DESTINATION__POSTGRES__CREDENTIALS__PASSWORD="secret"
```

**Note:** The section after `SOURCES__` must match the **Python module name** (the `.py` filename), not the source function name. See the [dlt credentials docs](https://dlthub.com/docs/general-usage/credentials/setup) for full naming rules.

Ensure `.env` is in `.gitignore`. Your orchestrator (Dagster, Airflow, etc.) or a `python-dotenv` call loads these at runtime.

In code, reference credentials with `dlt.secrets.value` (sensitive) or `dlt.config.value` (non-sensitive) as function parameter defaults. dlt resolves them automatically from environment variables:

```python
@dlt.source
def my_source(bucket_url: str = dlt.config.value):
    ...
```

Never hardcode credentials in pipeline code — use `dlt.secrets.value` or environment variables instead.

## Step 2: Define Table Configs

Each table config maps a file glob pattern to a destination table:

```python
TABLES_CONFIG = [
    {
        "file_glob": "sales/*.csv",          # Glob pattern relative to bucket root
        "table_name": "sales",                # Destination table name
        "file_type": "csv",                   # csv, jsonl, json, parquet, xlsx
        "file_hints": {                       # Hints for the filesystem reader
            "incremental": dlt.sources.incremental("modification_date"),
        },
        "pipe_hints": {                       # Hints for the destination table
            "write_disposition": "merge",
            "primary_key": ["transaction_id"],
            "columns": {
                "amount": {"data_type": "double"},
                "transaction_date": {"data_type": "date"},
                "modification_date": {"dedup_sort": "desc"},
            },
        },
    },
]
```

### Key Fields

- **`file_glob`**: Path pattern relative to bucket root. Supports `*`, `**`, `?`.
- **`file_type`**: Determines which transformer reads the file (csv, jsonl, json, parquet, xlsx).
- **`file_hints.incremental`**: Track `modification_date` to only process new/modified files.
- **`pipe_hints.columns`**: Explicit type hints for columns that need casting.
- **`pipe_hints.dedup_sort`**: When merging, use `desc` on `modification_date` to keep the latest version.

## Step 3: Build Transformers

Each file type needs a transformer function that reads files and yields records.

### CSV (with chunked reading)

```python
@dlt.transformer(name="read_csv")
def read_csv(items, chunksize=10000):
    import pandas as pd
    for file_item in items:
        with file_item.open() as f:
            for chunk in pd.read_csv(f, chunksize=chunksize):
                for record in chunk.to_dict(orient="records"):
                    record["modification_date"] = file_item["modification_date"]
                    record["file_name"] = file_item["file_name"]
                    yield record
```

### JSONL (newline-delimited JSON)

```python
@dlt.transformer(name="read_jsonl")
def read_jsonl(items):
    import json
    for file_item in items:
        with file_item.open() as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    record["modification_date"] = file_item["modification_date"]
                    record["file_name"] = file_item["file_name"]
                    yield record
```

### Parquet / Excel

Use `pandas.read_parquet()` or `pandas.read_excel()` — same pattern as CSV but without chunking.

### Metadata Injection

Always inject file metadata (`modification_date`, `file_name`) into records. This enables:
- **Dedup sorting**: Keep latest version of a record across file versions
- **Debugging**: Trace a record back to its source file
- **Incremental loading**: Track which files have been processed

## Step 4: Column Typing

CSV files are especially prone to type inference issues. Add explicit hints for:

| Problem | Solution |
|---------|----------|
| Numeric columns read as text | `{"data_type": "double"}` |
| Date strings not parsed | `{"data_type": "date"}` or `{"data_type": "timestamp"}` |
| ID columns with leading zeros | `{"data_type": "text"}` (prevent numeric cast) |
| Boolean columns as 0/1 | `{"data_type": "bool"}` |

```python
"columns": {
    "account_number": {"data_type": "text"},
    "amount": {"data_type": "double"},
    "transaction_date": {"data_type": "date"},
}
```

## Step 5: Write Dispositions

| Strategy | Use When | Config |
|----------|----------|--------|
| `merge` with `dedup_sort` | Incremental files that may overlap | `"write_disposition": "merge"` + `"modification_date": {"dedup_sort": "desc"}` |
| `replace` | Full snapshot files (always complete) | `"write_disposition": "replace"` |
| `append` | Immutable event logs | `"write_disposition": "append"` |

For merge with dedup, the primary key identifies the record and `dedup_sort` on `modification_date` ensures the latest file version wins when records overlap.

## Step 6: Backfill Strategy

For date-partitioned storage layouts (e.g. `gs://bucket/events/2024-01/*.jsonl`):

### Month-by-Month Iteration

```python
def generate_months(start, end):
    current = pendulum.parse(start).start_of("month")
    end_date = pendulum.parse(end).start_of("month")
    while current <= end_date:
        yield current.format("YYYY-MM")
        current = current.add(months=1)

for month in generate_months("2023-01", "2024-12"):
    files = filesystem(bucket_url=bucket_url, file_glob=f"{month}/*.jsonl")
    resource = files | read_jsonl
    pipeline.run(resource)
```

Benefits:
- **Memory-safe**: Processes one month at a time
- **Resumable**: If a month fails, rerun from that month
- **Visible progress**: Logs show which month is loading

## Step 7: Validate

1. **Test with one file** — verify the transformer reads and yields records correctly
2. **Check column types** — ensure explicit hints are applied
3. **Verify incremental** — run twice, confirm only new/modified files are processed
4. **Check dedup** — if using merge, confirm latest file version wins
5. **Test backfill** — for date-partitioned data, run a single month first

```bash
python my_pipeline.py
dlt pipeline my_pipeline show
```

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

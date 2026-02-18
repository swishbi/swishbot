"""
Generic Cloud File Storage Pipeline
=====================================
Covers loading data from cloud storage (Azure Blob, S3, GCS) and local
filesystems using dlt's filesystem verified source with custom transformers.

Supports: CSV, JSONL, JSON, Parquet, Excel
Patterns: Incremental loading, metadata injection, chunked reading, backfill

"""

import logging
import os
from collections.abc import Iterator
from typing import Any

import dlt
from dlt.common import pendulum

logger = logging.getLogger("dlt")


# ---------------------------------------------------------------------------
# Table configuration
# ---------------------------------------------------------------------------

# Each entry defines a file source to load. The file_hints configure the
# filesystem reader (globs, incremental tracking), and pipe_hints configure
# the destination table (write disposition, primary key, column types).

TABLES_CONFIG: list[dict[str, Any]] = [
    {
        "file_glob": "sales/*.csv",
        "table_name": "sales",
        "file_type": "csv",
        "file_hints": {
            "incremental": dlt.sources.incremental("modification_date"),
        },
        "pipe_hints": {
            "write_disposition": "merge",
            "primary_key": ["transaction_id", "line_number"],
            "columns": {
                "amount": {"data_type": "double"},
                "tax": {"data_type": "double"},
                "transaction_date": {"data_type": "date"},
                "modification_date": {"dedup_sort": "desc"},
            },
        },
    },
    {
        "file_glob": "events/*.jsonl",
        "table_name": "events",
        "file_type": "jsonl",
        "file_hints": {
            "incremental": dlt.sources.incremental("modification_date"),
        },
        "pipe_hints": {
            "write_disposition": "merge",
            "primary_key": ["event_id"],
            "columns": {
                "event_value": {"data_type": "double"},
                "event_date": {"data_type": "date"},
            },
        },
    },
    {
        "file_glob": "reports/*.xlsx",
        "table_name": "reports",
        "file_type": "xlsx",
        "pipe_hints": {
            "write_disposition": "replace",
        },
    },
    {
        "file_glob": "snapshots/*.parquet",
        "table_name": "snapshots",
        "file_type": "parquet",
        "pipe_hints": {
            "write_disposition": "replace",
        },
    },
]


# ---------------------------------------------------------------------------
# Transformer functions (one per file type)
# ---------------------------------------------------------------------------

@dlt.transformer(name="read_csv")
def read_csv(items, chunksize: int = 10000):
    """Read CSV files with chunked pandas reader for memory efficiency.

    Injects file metadata (modification_date, file_name) into each record.
    Uses pandas for type inference and chunked reading of large files.
    """
    import pandas as pd

    for file_item in items:
        with file_item.open() as f:
            for chunk in pd.read_csv(f, chunksize=chunksize):
                for record in chunk.to_dict(orient="records"):
                    record["modification_date"] = file_item["modification_date"]
                    record["file_name"] = file_item["file_name"]
                    yield record


@dlt.transformer(name="read_jsonl")
def read_jsonl(items):
    """Read JSONL (newline-delimited JSON) files line by line.

    Each line is a separate JSON object. Injects file metadata.
    """
    import json

    for file_item in items:
        with file_item.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                record["modification_date"] = file_item["modification_date"]
                record["file_name"] = file_item["file_name"]
                yield record


@dlt.transformer(name="read_json")
def read_json(items):
    """Read JSON files (array of objects or single object).

    Handles both JSON arrays and single objects. Injects file metadata.
    """
    import json

    for file_item in items:
        with file_item.open() as f:
            data = json.loads(f.read())

        records = data if isinstance(data, list) else [data]
        for record in records:
            record["modification_date"] = file_item["modification_date"]
            record["file_name"] = file_item["file_name"]
            yield record


@dlt.transformer(name="read_excel")
def read_excel(items, sheet_name: str | None = None):
    """Read Excel files with optional sheet selection.

    Uses pandas for reading. If sheet_name is None, reads the first sheet.
    For multi-sheet workbooks, call separately per sheet or iterate sheets.
    """
    import pandas as pd

    for file_item in items:
        with file_item.open() as f:
            df = pd.read_excel(f, sheet_name=sheet_name or 0)
            for record in df.to_dict(orient="records"):
                record["modification_date"] = file_item["modification_date"]
                record["file_name"] = file_item["file_name"]
                yield record


@dlt.transformer(name="read_parquet")
def read_parquet(items):
    """Read Parquet files. Injects file metadata."""
    import pandas as pd

    for file_item in items:
        with file_item.open() as f:
            df = pd.read_parquet(f)
            for record in df.to_dict(orient="records"):
                record["modification_date"] = file_item["modification_date"]
                record["file_name"] = file_item["file_name"]
                yield record


# Map file types to transformer functions
READERS = {
    "csv": read_csv,
    "jsonl": read_jsonl,
    "json": read_json,
    "xlsx": read_excel,
    "parquet": read_parquet,
}


# ---------------------------------------------------------------------------
# Source definition
# ---------------------------------------------------------------------------

@dlt.source(name="filesystem_example", max_table_nesting=0)
def filesystem_source(
    bucket_url: str = dlt.config.value,
    tables_config: list[dict[str, Any]] | None = None,
) -> Iterator[Any]:
    """Cloud file storage source.

    Reads files from Azure Blob, S3, GCS, or local filesystem and loads
    them into the destination using type-specific transformer functions.

    Args:
        bucket_url: Cloud storage URL. Examples:
            - Azure: "az://container-name"
            - S3: "s3://bucket-name"
            - GCS: "gs://bucket-name"
            - Local: "/path/to/directory" or "file:///path/to/directory"
        tables_config: List of table configuration dicts. Defaults to TABLES_CONFIG.
    """
    from dlt.sources.filesystem import filesystem

    config = tables_config or TABLES_CONFIG

    for table_config in config:
        file_type = table_config["file_type"]
        reader_fn = READERS.get(file_type)

        if not reader_fn:
            logger.warning(f"No reader for file type: {file_type}")
            continue

        # Create filesystem resource for this file glob
        files = filesystem(
            bucket_url=bucket_url,
            file_glob=table_config["file_glob"],
            **(table_config.get("file_hints") or {}),
        )

        # Pipe files through the type-specific transformer
        resource = files | reader_fn

        # Apply table-level hints (write disposition, primary key, columns)
        pipe_hints = table_config.get("pipe_hints", {})
        resource.apply_hints(
            table_name=table_config["table_name"],
            **pipe_hints,
        )

        yield resource


# ---------------------------------------------------------------------------
# Backfill pattern (date-partitioned directories)
# ---------------------------------------------------------------------------

def generate_months(start: str, end: str) -> Iterator[str]:
    """Generate YYYY-MM strings for each month in the range (inclusive).

    Use for backfilling date-partitioned storage layouts like:
    gs://bucket/events/2024-01/*.jsonl
    gs://bucket/events/2024-02/*.jsonl
    """
    current = pendulum.parse(start).start_of("month")
    end_date = pendulum.parse(end).start_of("month")
    while current <= end_date:
        yield current.format("YYYY-MM")
        current = current.add(months=1)


def backfill_by_month(
    bucket_url: str,
    start_month: str,
    end_month: str,
    file_pattern: str = "*.jsonl",
    table_name: str = "events",
    pipeline_name: str = "filesystem_backfill",
    destination: str = "postgres",
    dataset_name: str = "raw_files",
) -> None:
    """Backfill data from date-partitioned cloud storage month by month.

    Expects directory structure: {bucket_url}/{YYYY-MM}/{files}
    Loads one month at a time to manage memory and provide progress visibility.

    Pattern extracted from GA4 BigQuery export to GCS.
    """
    from dlt.sources.filesystem import filesystem

    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=destination,
        dataset_name=dataset_name,
        progress="log",
    )

    for month in generate_months(start_month, end_month):
        logger.info(f"Backfilling {month}...")

        files = filesystem(
            bucket_url=bucket_url,
            file_glob=f"{month}/{file_pattern}",
        )

        reader_fn = READERS.get(
            file_pattern.rsplit(".", 1)[-1],
            read_jsonl,
        )
        resource = files | reader_fn
        resource.apply_hints(
            table_name=table_name,
            write_disposition="merge",
            primary_key=["event_id"],
        )

        load_info = pipeline.run(resource)
        print(f"{month}: {load_info}")


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def load_filesystem() -> None:
    bucket_url = os.getenv("BUCKET_URL", "")
    if not bucket_url:
        raise ValueError("BUCKET_URL environment variable is required")

    source = filesystem_source(bucket_url=bucket_url)

    pipeline = dlt.pipeline(
        pipeline_name="filesystem_pipeline",
        destination="postgres",  # Replace with your destination
        dataset_name="raw_files",
        progress="log",
    )

    load_info = pipeline.run(source)
    print(load_info)


if __name__ == "__main__":
    load_filesystem()

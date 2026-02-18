"""Shared dlt destination configuration.

Uses environment variables to select the destination. Falls back to DuckDB
for local development when Snowflake credentials are not set.
"""

import os

import dlt


def _get_destination():
    """Return the dlt destination based on environment variables."""
    if os.getenv("DESTINATION__SNOWFLAKE__CREDENTIALS__ACCOUNT"):
        return dlt.destinations.snowflake()
    return dlt.destinations.duckdb()


destination = _get_destination()

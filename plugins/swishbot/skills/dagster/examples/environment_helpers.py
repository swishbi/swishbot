"""
Environment Helpers
====================
Centralized environment detection for Dagster Cloud. Place at:
orchestration/utils/environment_helpers.py

All env-specific config should derive from get_env() rather than checking
DAGSTER_CLOUD_* variables directly.
"""

import os


def get_env() -> str:
    """Determine the current environment based on Dagster Cloud variables.

    Returns: 'BRANCH', 'PROD', or 'LOCAL'.
    """
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "prod":
        return "PROD"
    return "LOCAL"


def get_dbt_target() -> str:
    """Determine dbt target based on environment."""
    env = get_env()
    if env == "PROD":
        return "prod"
    elif env == "BRANCH":
        return "ci"
    return "dev"


def get_kind() -> str:
    """Determine the storage kind (warehouse type) based on environment."""
    env = get_env()
    if env in ["PROD", "BRANCH"]:
        return "snowflake"  # Or "databricks", "bigquery", etc.
    return "duckdb"


def get_database_for_environment(default_database: str = "analytics") -> str:
    """Return the database name for the current environment."""
    env = get_env()
    if env == "PROD":
        return default_database
    return f"{default_database}_dev"


def get_schema_for_environment(default_schema: str = "marts") -> str:
    """Return the schema name for the current environment.

    Local dev uses DBT_SANDBOX_SCHEMA (e.g. dbt_ephillips).
    Branch deployments use dbt_ci.
    Production uses the default schema.
    """
    env = get_env()
    if env == "LOCAL":
        return os.getenv("DBT_SANDBOX_SCHEMA", default_schema)
    elif env == "BRANCH":
        return "dbt_ci"
    return default_schema

"""Environment Helpers.

Centralized environment detection for Dagster Cloud. All env-specific config
should derive from get_env() rather than checking DAGSTER_CLOUD_* variables directly.
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
        return "snowflake"
    return "duckdb"

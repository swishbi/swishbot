# Set Up Dagster Project

Bootstrap a new Dagster project with the concept-based layout for Dagster+ Serverless.

**Reference examples:** `examples/definitions.py`, `examples/pyproject.toml`, `examples/dagster_cloud.yaml`

## Step 1: Create Directory Structure

```
my-project/
├── ingestion/              # dlt pipelines
│   └── __init__.py
├── transformation/         # dbt project
├── orchestration/          # Dagster
│   ├── __init__.py
│   ├── definitions.py
│   ├── defs/
│   │   └── __init__.py
│   └── utils/
│       ├── __init__.py
│       └── environment_helpers.py
├── tests/
│   └── __init__.py
├── pyproject.toml
├── dagster_cloud.yaml
├── .env
├── .gitignore
└── Dockerfile
```

Do **not** use `dagster project scaffold` or `dg init` — they generate the default `src/` layout. Create this structure manually.

## Step 2: Configure pyproject.toml

```toml
[project]
name = "my-project"
requires-python = ">=3.12,<3.14"
version = "0.1.0"
dependencies = [
    "dagster",
    "dagster-cloud",
    "dagster-dbt",
    "dagster-dlt",
    "dbt-snowflake",          # Or dbt-postgres, dbt-bigquery, etc.
    "dlt[az]",                # Or dlt[s3], dlt[gs], etc.
    "pandas",
]

[dependency-groups]
dev = [
    "dagster-webserver",
    "dagster-dg-cli",
    "dbt-duckdb",             # Local dev destination
    "dlt[duckdb,workspace]",
    "pytest",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["orchestration"]
force-include = { "pyproject.toml" = "pyproject.toml" }

[tool.dg]
directory_type = "project"

[tool.dg.project]
root_module = "orchestration"
code_location_target_module = "orchestration.definitions"
registry_modules = ["orchestration.defs.*"]

[tool.dg.project.python_environment]
uv_managed = true
```

Key points:
- **`packages = ["orchestration"]`** — only the orchestration layer is the Python package
- **`root_module = "orchestration"`** — Dagster looks here for definitions
- **`registry_modules`** — tells `dg` where to discover components
- **`force-include`** — ensures pyproject.toml is available in the wheel (needed for Dagster+ Serverless)

## Step 3: Write definitions.py

```python
from pathlib import Path
from dagster import definitions, load_from_defs_folder

@definitions
def defs():
    return load_from_defs_folder(project_root=Path(__file__).parent.parent)
```

This auto-discovers all `defs.yaml` files in `orchestration/defs/` and its subdirectories. No manual registration needed.

## Step 4: Configure dagster_cloud.yaml

```yaml
locations:
  - location_name: my_project
    code_source:
      module_name: orchestration.definitions
```

This tells Dagster+ Serverless where to find the definitions entry point.

## Step 5: Add Environment Helpers

Create `orchestration/utils/environment_helpers.py`:

```python
import os

def get_env() -> str:
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "prod":
        return "PROD"
    return "LOCAL"

def get_dbt_target() -> str:
    env = get_env()
    if env == "PROD":
        return "prod"
    elif env == "BRANCH":
        return "ci"
    return "dev"

def get_kind() -> str:
    env = get_env()
    if env in ["PROD", "BRANCH"]:
        return "snowflake"  # Or your cloud warehouse
    return "duckdb"
```

These helpers centralize environment-aware logic. Every component and resource should derive env-specific config from `get_env()` rather than checking `DAGSTER_CLOUD_*` variables directly.

## Step 6: Set Up .env

```bash
# .env — MUST be in .gitignore

# Dagster Cloud (set automatically in Dagster+ Serverless)
# DAGSTER_CLOUD_DEPLOYMENT_NAME=prod
# DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT=0

# Source credentials
SOURCES__MY_PIPELINE__API_KEY="your-api-key"

# Destination credentials
DESTINATION__SNOWFLAKE__CREDENTIALS__ACCOUNT="your-account"
DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE="analytics"
DESTINATION__SNOWFLAKE__CREDENTIALS__WAREHOUSE="LOADING"
DESTINATION__SNOWFLAKE__CREDENTIALS__ROLE="LOADER"
DESTINATION__SNOWFLAKE__CREDENTIALS__USER="your-user"
DESTINATION__SNOWFLAKE__CREDENTIALS__PASSWORD="your-password"
```

## Step 7: Validate

```bash
# Install dependencies
uv sync

# Start Dagster dev server
dg dev

# Verify in browser at http://localhost:3000
# - Global asset graph loads
# - No import errors in the logs
```

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

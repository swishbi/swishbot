# Add dbt Component

Wire a dbt project into Dagster using `DbtProjectComponent`.

**Reference examples:** `examples/dbt_defs.yaml`, `examples/dbt_template_vars.py`

## Prerequisites

- A working dbt project in `transformation/` (see the **dbt-staging** skill)
- Dagster project set up with the concept-based layout (see **Set Up Project** workflow)
- `dagster-dbt` in your dependencies

## Step 1: Create the Component Directory

```
orchestration/defs/transformation/dbt/
├── defs.yaml             # DbtProjectComponent definition
└── template_vars.py      # Automation condition logic
```

## Step 2: Write defs.yaml

```yaml
type: dagster_dbt.DbtProjectComponent

template_vars_module: .template_vars

attributes:
  project:
    project_dir: "{{ project_root }}/transformation"
    target: >-
      {%- if env('DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT','') == '1' -%}ci
      {%- elif env('DAGSTER_CLOUD_DEPLOYMENT_NAME','') == 'prod' -%}prod
      {%- else -%}dev
      {%- endif -%}
  translation:
    key: |
      {%- if node.resource_type == 'source' -%}
        {{ node.schema }}/{{ node.name }}
      {%- else -%}
        {{ node.name }}
      {%- endif -%}
    automation_condition: "{{ get_automation_condition(node) }}"
  translation_settings:
    enable_code_references: true
    enable_source_tests_as_checks: true
```

Key points:
- **`project_dir`** — points to the dbt project as a sibling directory using `{{ project_root }}`
- **`target`** — dynamically selects `dev`, `ci`, or `prod` based on Dagster Cloud environment
- **`key` for sources** — uses `schema/name` so dbt sources link to dlt-loaded asset keys (e.g. `centerpoint/customers` matches both the dlt asset and the dbt source)
- **`key` for models** — uses just `name` for clean asset keys
- **`enable_code_references`** — links assets to source code in the Dagster UI
- **`enable_source_tests_as_checks`** — dbt source tests appear as asset checks

## Step 3: Write template_vars.py

```python
import dagster as dg
from typing import Any, Callable, Mapping

@dg.template_var
def get_automation_condition() -> Callable[[Mapping[str, Any]], Any]:
    """Determine automation condition based on node properties."""
    def _get_automation_condition(node: Mapping[str, Any]) -> Any:
        resource_type = node.get("resource_type", "")
        depends_on = node.get("depends_on", {})
        has_upstream = bool(depends_on.get("nodes", []))

        if resource_type == "seed" or not has_upstream:
            # Seeds and root nodes run on a schedule
            return dg.AutomationCondition.on_cron("0 5 * * *")
        else:
            # Everything else runs eagerly when dependencies complete
            return dg.AutomationCondition.eager()

    return _get_automation_condition
```

This creates a cascade: dlt sources run on cron → dbt sources (no upstream in dbt) run on cron → staging/intermediate/mart models run eagerly as their dependencies complete.

## Step 4: Ensure Source Keys Align

The critical wiring between dlt and dbt is the **asset key alignment**. For dbt to depend on dlt-loaded tables:

| Layer | Asset Key | How It's Set |
|-------|-----------|-------------|
| dlt asset | `centerpoint/customers` | `key: "{{ resource.source_name }}/{{ resource.name }}"` in dlt defs.yaml |
| dbt source | `centerpoint/customers` | `key: "{{ node.schema }}/{{ node.name }}"` in dbt defs.yaml |
| dbt model | `stg_centerpoint__customers` | `key: "{{ node.name }}"` in dbt defs.yaml |

The dbt source's `schema` must match the dlt source's `source_name`, and the dbt source's `name` must match the dlt resource's `name`. This is how Dagster links the dlt asset to the dbt source dependency.

## Step 5: Configure dbt Targets

In `transformation/profiles.yml`, define targets that match the Dagster environment:

```yaml
my_project:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "{{ env_var('DBT_DUCKDB_PATH', 'analytics.duckdb') }}"
    ci:
      type: snowflake
      account: "{{ env_var('DESTINATION__SNOWFLAKE__CREDENTIALS__ACCOUNT') }}"
      database: analytics
      schema: dbt_ci
      # ...
    prod:
      type: snowflake
      account: "{{ env_var('DESTINATION__SNOWFLAKE__CREDENTIALS__ACCOUNT') }}"
      database: analytics
      schema: "{{ env_var('DBT_SCHEMA', 'staging') }}"
      # ...
```

## Step 6: Validate

1. Start Dagster dev: `dg dev`
2. Check the asset graph — dbt models should appear with dependencies linking back to dlt assets
3. Verify source tests appear as asset checks
4. Materialize a staging model to test the full pipeline

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

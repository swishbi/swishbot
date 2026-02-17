# Add dlt Component

Wire a dlt pipeline into Dagster as assets using `DltLoadCollectionComponent`.

**Reference examples:** `examples/dlt_component.py`, `examples/dlt_defs.yaml`, `examples/dlt_loads.py`, `examples/dlt_resources.py`

## Prerequisites

- A working dlt pipeline in `ingestion/<source>/` (see the **dlt-pipelines** skill)
- Dagster project set up with the concept-based layout (see **Set Up Project** workflow)
- `dagster-dlt` in your dependencies

## Step 1: Create the Component Directory

```
orchestration/defs/ingestion/dlt/
├── __init__.py
├── component.py          # Custom component (shared across all dlt sources)
├── resources.py          # DagsterDltResource
├── <source>/
│   ├── defs.yaml         # Component definition
│   └── loads.py          # dlt source + pipeline instances
└── <another-source>/
    ├── defs.yaml
    └── loads.py
```

The `component.py` and `resources.py` are shared by all dlt sources. Each source gets its own subdirectory with a `defs.yaml` and `loads.py`.

## Step 2: Define the DagsterDltResource

Create `orchestration/defs/ingestion/dlt/resources.py`:

```python
import dagster as dg
from dagster.components import definitions
from dagster_dlt import DagsterDltResource

@definitions
def defs() -> dg.Definitions:
    return dg.Definitions(
        resources={"dlt": DagsterDltResource()},
    )
```

This registers the `dlt` resource globally so all dlt components can use it.

## Step 3: Create loads.py for the Source

Create `orchestration/defs/ingestion/dlt/<source>/loads.py`:

```python
import dlt
from ingestion.destination import destination
from ingestion.<source>.<source>_pipeline import <source>_source

dlthub_dlt_<source>_source = <source>_source()
dlthub_dlt_<source>_pipeline = dlt.pipeline(
    pipeline_name="<source>_pipeline",
    destination=destination,
    dataset_name="<source>",
    progress="log",
)
```

Key points:
- Import the dlt source function from `ingestion/` (the sibling directory)
- Instantiate the source and pipeline as module-level variables — the component YAML references them
- `dataset_name` maps to the destination schema

## Step 4: Write defs.yaml

Create `orchestration/defs/ingestion/dlt/<source>/defs.yaml`:

```yaml
type: orchestration.defs.ingestion.dlt.component.CustomDltLoadCollectionComponent

attributes:
  loads:
    - source: .loads.dlthub_dlt_<source>_source
      pipeline: .loads.dlthub_dlt_<source>_pipeline
      translation:
        automation_condition: "{{ cron_not_in_progress('0 5 * * *', 'America/New_York') }}"
        group_name: "{{ resource.source_name }}"
        description: "Loads data from the {{ resource.name }} table using the <Source> API."
        key: "{{ resource.source_name }}/{{ resource.name }}"
        deps: []
        metadata:
          resource_name: "{{ resource.name }}"
          pipeline_name: "{{ pipeline.pipeline_name }}"

requirements:
  env:
    - SOURCES__<SOURCE>_PIPELINE__API_KEY
    - DESTINATION__SNOWFLAKE__CREDENTIALS__ACCOUNT
```

Key points:
- **`type`** — use your custom component class (see Step 5), or the base `dagster_dlt.DltLoadCollectionComponent`
- **`.loads.`** prefix — dot-relative import from the same directory
- **`automation_condition`** — `cron_not_in_progress` runs on schedule but skips if the previous run hasn't finished
- **`key`** — `source_name/resource_name` creates a two-level asset key
- **`requirements.env`** — declares required environment variables; Dagster UI warns if missing

## Step 5: Create Custom Component (Optional but Recommended)

Create `orchestration/defs/ingestion/dlt/component.py`:

```python
from collections import defaultdict
from collections.abc import Mapping
from typing import Any

import dagster as dg
import dagster.components as dg_components
from dagster_dlt import DagsterDltTranslator
from dagster_dlt.translator import DltResourceTranslatorData
from dagster_dlt.components.dlt_load_collection.component import DltLoadCollectionComponent


class CustomDagsterDltTranslator(DagsterDltTranslator):
    """Override asset key mapping: source_name/resource_name instead of default."""
    def get_asset_spec(self, data: DltResourceTranslatorData) -> dg.AssetSpec:
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(
            key=dg.AssetKey([data.resource.source_name, data.resource.name]),
        )


class CustomDltLoadCollectionComponent(DltLoadCollectionComponent):
    """Extend base component with automation conditions and dependency grouping."""

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        def _cron_not_in_progress(
            cron_schedule: str = "0 0 * * *",
            timezone: str = "UTC",
        ) -> dg.AutomationCondition:
            return (
                dg.AutomationCondition.cron_tick_passed(cron_schedule, timezone)
                & ~dg.AutomationCondition.in_progress()
            )
        return {"cron_not_in_progress": _cron_not_in_progress}

    def build_defs(self, context: dg_components.ComponentLoadContext) -> dg.Definitions:
        defs = super().build_defs(context)

        # Group external dependencies by group name for asset graph clarity
        deps_by_group: dict[str, set[dg.AssetKey]] = defaultdict(set)
        for asset in defs.assets or []:
            if isinstance(asset, dg.AssetsDefinition):
                for asset_key, deps in asset.asset_deps.items():
                    group_name = asset.group_names_by_key[asset_key]
                    deps_by_group[group_name].update(deps)

        specs = []
        for group_name, deps in deps_by_group.items():
            specs.extend([dg.AssetSpec(key=dep, group_name=group_name) for dep in deps])

        return dg.Definitions.merge(defs, dg.Definitions(assets=specs))
```

This component adds:
- **`cron_not_in_progress`** — automation condition available in defs.yaml templates
- **Dependency grouping** — external dependencies are grouped in the asset graph for clarity
- Extend `get_additional_scope()` to add more template variables as needed

## Step 6: Validate

1. Start Dagster dev: `dg dev`
2. Check the asset graph — dlt resources should appear as assets under the source group
3. Materialize a single asset to test the pipeline
4. Verify data arrived in the destination

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

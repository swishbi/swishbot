# Add Custom Component

Extend a base Dagster component with custom behavior — translators, automation conditions, partitioning, or asset specs.

**Reference examples:** `examples/dlt_component.py`

## When to Customize

| Need | Solution |
|------|----------|
| Custom asset keys | Override `get_asset_spec()` in a translator class |
| Automation conditions in YAML | Add to `get_additional_scope()` on the component |
| Multi-tenant partitioning | Add `partitions_def` and extend the component |
| Custom dependency grouping | Override `build_defs()` on the component |
| Environment-aware config | Use template variables with `@dg.template_var` |

## Pattern 1: Custom Translator

Override how dlt resources or dbt nodes map to Dagster asset keys and specs.

### dlt Translator

```python
from dagster_dlt import DagsterDltTranslator
from dagster_dlt.translator import DltResourceTranslatorData
import dagster as dg

class CustomDagsterDltTranslator(DagsterDltTranslator):
    def get_asset_spec(self, data: DltResourceTranslatorData) -> dg.AssetSpec:
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(
            key=dg.AssetKey([data.resource.source_name, data.resource.name]),
        )
```

Use `replace_attributes()` to modify specific fields while keeping defaults for everything else.

## Pattern 2: Additional Scope (Template Variables for YAML)

Expose Python functions as template variables in `defs.yaml`:

```python
class CustomDltLoadCollectionComponent(DltLoadCollectionComponent):
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
```

Now usable in YAML:
```yaml
automation_condition: "{{ cron_not_in_progress('0 5 * * *', 'America/New_York') }}"
```

## Pattern 3: Template Variables Module

For dbt components, use `@dg.template_var` in a `template_vars.py` module:

```python
import dagster as dg
from typing import Any, Callable, Mapping

@dg.template_var
def get_automation_condition() -> Callable[[Mapping[str, Any]], Any]:
    def _get_automation_condition(node: Mapping[str, Any]) -> Any:
        resource_type = node.get("resource_type", "")
        depends_on = node.get("depends_on", {})
        has_upstream = bool(depends_on.get("nodes", []))

        if resource_type == "seed" or not has_upstream:
            return dg.AutomationCondition.on_cron("0 5 * * *")
        else:
            return dg.AutomationCondition.eager()

    return _get_automation_condition
```

Reference in defs.yaml:
```yaml
template_vars_module: .template_vars
```

## Pattern 4: Overriding build_defs

Override `build_defs()` to modify the final definitions before Dagster loads them. Common use: grouping external dependencies.

```python
class CustomDltLoadCollectionComponent(DltLoadCollectionComponent):
    def build_defs(self, context: dg_components.ComponentLoadContext) -> dg.Definitions:
        defs = super().build_defs(context)

        # Group external dependencies by group name
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

## Pattern 5: Partitioned Assets (Multi-Tenant)

For sources that need to run separately per tenant/company:

```python
import dagster as dg

# Define partitions from environment
companies = os.getenv("SOURCE_COMPANIES", "").split(",")
partitions = dg.StaticPartitionsDefinition(companies)

# In the component, add partitions_def to asset generation
```

In `defs.yaml`, reference the partition definition via a template variable:

```yaml
attributes:
  loads:
    - source: .loads.my_source
      pipeline: .loads.my_pipeline
      partitions_def: "{{ my_partitions }}"
```

## Guidelines

- **Start with the base component** — only customize when the default behavior doesn't work
- **Prefer `get_additional_scope()`** over `build_defs()` — scope additions are additive and less likely to break
- **Keep `component.py` shared** — one custom component class per integration type (dlt, dbt, Power BI), not per source
- **Test locally first** — run `dg dev` and verify the asset graph before deploying

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

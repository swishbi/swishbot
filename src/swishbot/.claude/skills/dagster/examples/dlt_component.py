"""
Custom dlt Component
=====================
Extends DltLoadCollectionComponent with:
- Custom asset key translator (source_name/resource_name)
- cron_not_in_progress automation condition for YAML templates
- Dependency grouping in the asset graph
"""

from collections import defaultdict
from collections.abc import Mapping
from typing import Any

import dagster as dg
import dagster.components as dg_components
from dagster_dlt import DagsterDltTranslator
from dagster_dlt.components.dlt_load_collection.component import DltLoadCollectionComponent
from dagster_dlt.translator import DltResourceTranslatorData


class CustomDagsterDltTranslator(DagsterDltTranslator):
    """Override asset key mapping to use source_name/resource_name."""

    def get_asset_spec(self, data: DltResourceTranslatorData) -> dg.AssetSpec:
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(
            key=dg.AssetKey([data.resource.source_name, data.resource.name]),
        )


class CustomDltLoadCollectionComponent(DltLoadCollectionComponent):
    """Extend base dlt component with automation conditions and dependency grouping."""

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

"""Custom Power BI Component.

Extends PowerBIWorkspaceComponent with:
- Upstream asset dependencies derived from semantic model table references
- Eager automation condition for semantic models
"""

import dagster as dg
from dagster_powerbi.components.power_bi_workspace.component import PowerBIWorkspaceComponent
from dagster_powerbi.translator import PowerBIContentType, PowerBITranslatorData

from orchestration.utils.string_helpers import to_snake_case


class CustomPowerBIWorkspaceComponent(PowerBIWorkspaceComponent):
    """Custom PowerBIWorkspaceComponent that sets upstream dependencies
    and sets the automation condition to eager for semantic models.
    """

    def get_asset_spec(self, data: PowerBITranslatorData) -> dg.AssetSpec:
        base_asset_spec = super().get_asset_spec(data)

        if data.content_type == PowerBIContentType.SEMANTIC_MODEL:
            upstream_table_deps = [
                dg.AssetKey([to_snake_case(table.get("name"))])
                for table in data.properties.get("tables", [])
                if table.get("name")
            ]
            return base_asset_spec.replace_attributes(
                deps=upstream_table_deps,
                automation_condition=dg.AutomationCondition.eager(),
            )

        return base_asset_spec

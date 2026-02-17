"""
dbt Template Variables
=======================
Provides automation condition logic for dbt nodes. Place at:
orchestration/defs/transformation/dbt/template_vars.py

Seeds and root nodes (no upstream deps) run on a cron schedule.
Everything else runs eagerly when dependencies complete.
"""

import dagster as dg
from typing import Any, Callable, Mapping


@dg.template_var
def get_automation_condition() -> Callable[[Mapping[str, Any]], Any]:
    """Returns a function that determines automation condition based on node properties."""

    def _get_automation_condition(node: Mapping[str, Any]) -> Any:
        resource_type = node.get("resource_type", "")
        depends_on = node.get("depends_on", {})
        has_upstream = bool(depends_on.get("nodes", []))

        if resource_type == "seed" or not has_upstream:
            return dg.AutomationCondition.on_cron("0 5 * * *")
        else:
            return dg.AutomationCondition.eager()

    return _get_automation_condition

"""Custom dlt Components.

Extends DltLoadCollectionComponent with:
- Custom asset key translator (source_name/resource_name)
- cron_not_in_progress automation condition for YAML templates
- Dependency grouping in the asset graph
- Partitioned load support with backfill/incremental modes
"""

import datetime
from collections import defaultdict
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

import dagster as dg
import dagster.components as dg_components
from dagster import (
    AssetExecutionContext,
    AssetKey,
    BackfillPolicy,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    PartitionsDefinition,
    RunRequest,
    SensorDefinition,
    SensorEvaluationContext,
    SkipReason,
    WeeklyPartitionsDefinition,
    sensor,
)
from dagster_dlt import DagsterDltResource, DagsterDltTranslator
from dagster_dlt.components.dlt_load_collection.component import DltLoadCollectionComponent
from dagster_dlt.translator import DltResourceTranslatorData
from dlt.common.time import ensure_pendulum_datetime


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
                dg.AutomationCondition.cron_tick_passed(cron_schedule, timezone) & ~dg.AutomationCondition.in_progress()
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


@dataclass
class DltPartitionedLoadComponent(DltLoadCollectionComponent):
    """A partitioned version of DltLoadCollectionComponent that adds partitioning support.

    Preserves the original source, pipeline, and translation from the base component
    while adding configurable partitioning patterns. This component can work with any
    DLT source that accepts partition parameters.
    """

    partition_type: Literal["daily", "weekly", "monthly", "hourly"] = field(default="daily")
    start_date: str = field(default="2025-01-01")
    timezone: str = field(default="UTC")
    max_partitions_per_run: int = field(default=1)
    partition_param_name: str = field(default="partition_date")
    source_module: str | None = field(default=None)
    source_function: str | None = field(default=None)
    allow_non_partitioned_runs: bool = field(default=True)

    # Incremental sensor configuration
    incremental_sensor_enabled: bool = field(default=False)
    incremental_sensor_cron: str = field(default="0 0 * * *")
    incremental_sensor_name: str | None = field(default=None)

    def __post_init__(self):
        """Validate component configuration after initialization."""
        if hasattr(super(), "__post_init__"):
            super().__post_init__()  # type: ignore
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate the component configuration parameters."""
        try:
            datetime.datetime.strptime(self.start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid start_date format: {self.start_date}. Expected format: YYYY-MM-DD")

        if self.max_partitions_per_run <= 0:
            raise ValueError(f"max_partitions_per_run must be positive, got: {self.max_partitions_per_run}")

        if not self.partition_param_name or not self.partition_param_name.isidentifier():
            raise ValueError(
                f"partition_param_name must be a valid Python identifier, got: {self.partition_param_name}"
            )

    def _create_partitions_def(self) -> PartitionsDefinition:
        """Create the appropriate partitions definition based on partition_type."""
        partition_classes = {
            "daily": DailyPartitionsDefinition,
            "weekly": WeeklyPartitionsDefinition,
            "monthly": MonthlyPartitionsDefinition,
            "hourly": HourlyPartitionsDefinition,
        }

        partition_class = partition_classes.get(self.partition_type)
        if not partition_class:
            raise ValueError(
                f"Unsupported partition_type: {self.partition_type}. "
                f"Must be one of: {', '.join(partition_classes.keys())}"
            )

        return partition_class(start_date=self.start_date, timezone=self.timezone)

    def _extract_partition_value(self, context: AssetExecutionContext) -> str | None:
        """Extract and format partition value from context.

        Returns the partition value in a format suitable for the DLT source,
        or None if no partition is available.
        """
        if not context.partition_key:
            return None

        try:
            if self.partition_type == "hourly":
                partition_datetime = datetime.datetime.fromisoformat(context.partition_key.replace("Z", "+00:00"))
                return partition_datetime.date().isoformat()
            else:
                datetime.datetime.strptime(context.partition_key, "%Y-%m-%d")
                return context.partition_key
        except (ValueError, TypeError):
            return context.partition_key

    def _get_source_function(self):
        """Dynamically import and return the source function."""
        if not self.source_module or not self.source_function:
            if self.loads and len(self.loads) > 0:
                return self.loads[0].source
            raise ValueError(
                "Either source_module and source_function must be specified, "
                "or source must be provided in loads configuration"
            )

        import importlib

        module = importlib.import_module(self.source_module)
        return getattr(module, self.source_function)

    def _build_incremental_sensor(
        self,
        asset_keys: list[AssetKey],
        sensor_name: str,
    ) -> SensorDefinition:
        """Build a sensor that triggers incremental (non-partitioned) runs.

        This sensor runs on a cron schedule and triggers the DLT load with the
        `dlt/mode: incremental` tag, which tells execute() to use dlt's internal
        cursor handling instead of partition-based date ranges.
        """
        cron_schedule = self.incremental_sensor_cron
        timezone = self.timezone

        @sensor(
            name=sensor_name,
            minimum_interval_seconds=60,
            default_status=dg.DefaultSensorStatus.STOPPED,
        )
        def incremental_load_sensor(context: SensorEvaluationContext) -> Iterator[RunRequest | SkipReason]:
            """Sensor that triggers incremental DLT loads on a cron schedule."""
            import pendulum

            try:
                from croniter import croniter  # type: ignore
            except ImportError:
                context.log.warning(
                    "croniter not installed. Install with: pip install croniter. Falling back to always triggering."
                )
                run_key = f"incremental_{pendulum.now(timezone).to_iso8601_string()}"
                yield RunRequest(
                    run_key=run_key,
                    tags={"dlt/mode": "incremental"},
                    asset_selection=asset_keys,
                )
                return

            now = pendulum.now(timezone)

            last_run_str = context.cursor or "1970-01-01T00:00:00+00:00"
            last_run_parsed = pendulum.parse(last_run_str)
            if hasattr(last_run_parsed, "naive"):
                last_run_dt = last_run_parsed.naive()  # type: ignore
            else:
                last_run_dt = datetime.datetime.fromisoformat(last_run_str.replace("Z", "+00:00"))

            cron = croniter(cron_schedule, last_run_dt)
            next_run = pendulum.instance(cron.get_next(datetime.datetime))

            if now >= next_run:
                run_key = f"incremental_{now.to_iso8601_string()}"
                context.log.info(f"Triggering incremental load for assets: {[str(k) for k in asset_keys]}")

                yield RunRequest(
                    run_key=run_key,
                    tags={"dlt/mode": "incremental"},
                    asset_selection=asset_keys,
                )

                context.update_cursor(now.to_iso8601_string())
            else:
                yield SkipReason(f"Next incremental run scheduled for {next_run.to_iso8601_string()}")

        return incremental_load_sensor

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        """Build definitions with partitioned assets and unique naming per partition type."""
        modified_loads = []

        for load_spec in self.loads:
            base_dataset = load_spec.pipeline.dataset_name or "sample_data"

            import dlt

            unique_pipeline = dlt.pipeline(
                pipeline_name=load_spec.pipeline.pipeline_name,
                destination=load_spec.pipeline.destination,
                dataset_name=base_dataset,
            )

            from dagster_dlt.components.dlt_load_collection.component import DltLoadSpecModel

            modified_load_spec = DltLoadSpecModel(
                pipeline=unique_pipeline,
                source=load_spec.source,
                translation=load_spec.translation,
            )
            modified_loads.append(modified_load_spec)

        original_loads = self.loads
        self.loads = modified_loads

        try:
            base_defs = super().build_defs(context)

            deps_by_group: dict[str, set[dg.AssetKey]] = defaultdict(set)
            for asset in base_defs.assets or []:
                if isinstance(asset, dg.AssetsDefinition):
                    for asset_key, deps in asset.asset_deps.items():
                        group_name = asset.group_names_by_key[asset_key]
                        deps_by_group[group_name].update(deps)

            specs = []
            for group_name, deps in deps_by_group.items():
                specs.extend([dg.AssetSpec(key=dep, group_name=group_name) for dep in deps])

            partitions_def = self._create_partitions_def()
            backfill_policy = BackfillPolicy(max_partitions_per_run=self.max_partitions_per_run)

            partitioned_assets = []
            for asset in base_defs.assets or []:
                if not isinstance(asset, dg.AssetsDefinition):
                    partitioned_assets.append(asset)
                    continue

                try:
                    partitioned_asset = dg.AssetsDefinition(
                        keys_by_input_name=asset.keys_by_input_name,
                        keys_by_output_name=asset.keys_by_output_name,
                        node_def=asset.node_def,
                        partitions_def=partitions_def,
                        backfill_policy=backfill_policy,
                        can_subset=asset.can_subset,
                        asset_deps=asset.asset_deps,
                        resource_defs=asset.resource_defs,
                        group_names_by_key=asset.group_names_by_key,
                        descriptions_by_key=asset.descriptions_by_key,
                        metadata_by_key=asset.metadata_by_key,
                        tags_by_key=asset.tags_by_key,
                    )
                    partitioned_assets.append(partitioned_asset)
                except Exception:
                    partitioned_assets.append(asset)

            asset_keys_for_sensor: list[AssetKey] = []
            for asset in partitioned_assets:
                if isinstance(asset, dg.AssetsDefinition):
                    asset_keys_for_sensor.extend(asset.keys)

            sensors_list = list(base_defs.sensors or [])
            if self.incremental_sensor_enabled and asset_keys_for_sensor:
                sensor_name = self.incremental_sensor_name or f"{self.loads[0].pipeline.pipeline_name}_incremental"
                incremental_sensor = self._build_incremental_sensor(
                    asset_keys=asset_keys_for_sensor,
                    sensor_name=sensor_name,
                )
                sensors_list.append(incremental_sensor)

            return dg.Definitions.merge(
                dg.Definitions(
                    assets=partitioned_assets,
                    resources=base_defs.resources,
                    jobs=base_defs.jobs,
                    schedules=base_defs.schedules,
                    sensors=sensors_list,
                    asset_checks=base_defs.asset_checks,
                    executor=base_defs.executor,
                    loggers=base_defs.loggers,
                ),
                dg.Definitions(assets=specs),
            )

        finally:
            self.loads = original_loads

    def _determine_execution_mode(self, context: AssetExecutionContext) -> str:
        """Determine whether to run in 'backfill' or 'incremental' mode.

        Mode determination priority:
        1. Explicit `dlt/mode` tag ('backfill' or 'incremental') -> highest priority
        2. Presence of `dagster/backfill_id` tag -> backfill mode
        3. Partition key present -> backfill mode
        4. No partition key -> incremental mode
        """
        mode_tag = context.run.tags.get("dlt/mode", "").lower()
        if mode_tag in ("backfill", "incremental"):
            return mode_tag

        if "dagster/backfill_id" in context.run.tags:
            return "backfill"

        return "backfill" if context.partition_key else "incremental"

    def execute(self, context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource):
        """Execute the DLT load with support for backfill and incremental modes.

        Supports two execution modes controlled via run tags or auto-detection:

        **Backfill mode** (explicit date range):
        - Triggered by: `dlt/mode: backfill` tag, Dagster backfill, or partition selection
        - Passes `start_date`/`end_date` to DLT source based on partition time window
        - Use for historical data loads or re-processing specific time periods

        **Incremental mode** (cursor-based):
        - Triggered by: `dlt/mode: incremental` tag or no partition selection
        - Passes no date params; DLT uses its internal cursor for incremental loading
        - Use for regular scheduled syncs to pick up new/updated records

        Run tags:
        - `dlt/mode: backfill` - Force backfill mode (requires partition selection)
        - `dlt/mode: incremental` - Force incremental mode (ignores partition even if selected)
        """
        mode = self._determine_execution_mode(context)

        context.log.info(
            f"Execution mode: {mode} | "
            f"Partition: {context.partition_key or 'None'} | "
            f"Tags: dlt/mode={context.run.tags.get('dlt/mode', 'auto')}, "
            f"dagster/backfill_id={'present' if 'dagster/backfill_id' in context.run.tags else 'absent'}"
        )

        if mode == "backfill":
            if not context.partition_key:
                raise ValueError(
                    "Backfill mode requires a partition selection. "
                    "Either select partitions in the UI or use tag 'dlt/mode: incremental' "
                    "to run with dlt's cursor-based incremental loading."
                )

            time_window = context.partition_time_window
            start_date = ensure_pendulum_datetime(time_window.start).to_iso8601_string()
            end_date = ensure_pendulum_datetime(time_window.end).to_iso8601_string()

            context.log.info(
                f"Backfill: Loading {self.partition_type} partition {context.partition_key} "
                f"({start_date} to {end_date})"
            )

            source_func = self._get_source_function()
            partitioned_source = source_func(start_date=start_date, end_date=end_date)  # type: ignore
            yield from dlt_pipeline_resource.run(context=context, dlt_source=partitioned_source)

        elif self.allow_non_partitioned_runs:
            context.log.info("Incremental: Using dlt's internal cursor handling (no date params passed)")
            yield from super().execute(context, dlt_pipeline_resource)

        else:
            raise ValueError(
                "Incremental runs are disabled for this component. "
                "Set allow_non_partitioned_runs=True in component config or select partitions for backfill."
            )

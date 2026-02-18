"""
dlt Resource Registration
==========================
Registers the DagsterDltResource globally so all dlt components can use it.
Place this at orchestration/defs/ingestion/dlt/resources.py.
"""

import dagster as dg
from dagster.components import definitions
from dagster_dlt import DagsterDltResource


@definitions
def defs() -> dg.Definitions:
    return dg.Definitions(
        resources={"dlt": DagsterDltResource()},
    )

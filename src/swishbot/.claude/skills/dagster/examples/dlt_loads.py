"""
dlt Loads File
===============
Instantiates the dlt source and pipeline as module-level variables that the
component YAML references. Place one of these per source at:
orchestration/defs/ingestion/dlt/<source>/loads.py
"""

import dlt

from ingestion.destination import destination
from ingestion.my_source.my_source_pipeline import my_source_source

# Module-level variables — referenced by defs.yaml as .loads.<name>
dlthub_dlt_my_source_source = my_source_source()
dlthub_dlt_my_source_pipeline = dlt.pipeline(
    pipeline_name="my_source_pipeline",
    destination=destination,
    dataset_name="my_source",
    progress="log",
)

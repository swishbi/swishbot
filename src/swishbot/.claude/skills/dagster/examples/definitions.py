"""
Dagster Definitions Entry Point
================================
Single entry point that Dagster loads on startup. Uses load_from_defs_folder()
to auto-discover all component definitions in orchestration/defs/.
"""

from pathlib import Path

from dagster import definitions, load_from_defs_folder


@definitions
def defs():
    return load_from_defs_folder(project_root=Path(__file__).parent.parent)

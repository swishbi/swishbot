# Generating Cubes From dbt: `cube_dbt`

`cube_dbt` (by Cube, MIT, on PyPI) reads dbt's `manifest.json` and renders cubes in Cube's Python/Jinja data-model layer.

Reference: https://docs.cube.dev/recipes/data-modeling/dbt

## What It Generates

- `model.as_cube()`: the cube's name and `sql_table`, from the model's relation
- `model.as_dimensions()`: one dimension per dbt column, typed from the column's `data_type`, described from its dbt description
- A primary key, from a column tagged `primary_key` or a single column with `unique` and `not_null` tests

## What Stays Hand-Written

Measures, joins, pre-aggregations, views and access policies. Those carry the business meaning and the security boundary, so they should be written deliberately anyway.

## When It Pays Off

- Many marts, with columns that change often
- Cube reads the same database relation dbt builds
- Every mart column declares `data_type` in its YAML

## When It Doesn't

- **Cube reads a different file or database than dbt builds into** (for example a published DuckDB copy): `sql_table` must be overridden for every cube.
- **Composite keys** (statement marts keyed month × account): the primary key is still hand-written.
- **Columns without `data_type`** become `string` dimensions silently, so a date loses its time dimension.
- **Self-hosted Docker:** the image needs the package installed and `manifest.json` available where Cube compiles the model, which means a `dbt parse` in the build, not a committed manifest.
- **View contracts:** a dbt column rename renames the generated member, so every view needs an alias to keep its public name.

## The Lighter Alternative

A CI test that reads `manifest.json` and the hand-written cube YAML, and fails when a cube names a missing mart or column or a time dimension isn't a date (see [`../workflows/test-the-model.md`](../workflows/test-the-model.md), Step 5). It gives most of the drift protection with no Python in the Cube image.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

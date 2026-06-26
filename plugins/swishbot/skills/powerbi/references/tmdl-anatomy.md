# TMDL Anatomy

Reference for the structure of PBIP semantic-model files. Read this before attempting any file-based TMDL editing — the [Edit TMDL at Scale](../workflows/edit-tmdl-at-scale.md) workflow assumes everything here.

## PBIP / TMDL fundamentals

- A **PBIP semantic model is a folder of TMDL files**: `definition/tables/*.tmdl` (one file per table), with `_Measures.tmdl` as the home table for measures. They are **plain text and Claude-editable** — no Power BI Desktop required for authoring.
- **Encoding is UTF-8 with CRLF.** Anything that touches the file must preserve this. In Python, always read with `open(path, "rb").read().decode("utf-8")` — text-mode `open()` silently translates CRLF→LF and breaks every `split("\r\n")` downstream.
- **Power BI Desktop re-saves renormalize the file.** Blank lines inside expressions come back as `\t\t\t` (tab-indented), while tool-written content is `rstrip`ped. Both are valid TMDL. Tooling must treat the **current bytes** as the source of truth and never assume the file looks like it did last session.

## Measure block grammar

Each measure block, in order:

1. Optional `///` **description** lines at `\t` indent. Stacked `///` lines concatenate into one description.
2. The `\tmeasure 'Name' =` **header**. Multi-line DAX containing special characters is wrapped in triple-backtick fences.
3. The **expression body** at `\t\t\t` indent.
4. **Properties** at `\t\t` indent: `formatString`, `displayFolder`, `lineageTag`.
5. Blank-line-separated `annotation` lines.

Blocks are separated by a single empty line.

Header regex for parsing: `^\tmeasure (?:'([^']*)'|(\S+)) =`. To capture a block's description, walk **back** from the header over contiguous `\t///` lines. A block ends at the next block's first description line, or at the partition anchor.

## `lineageTag` uniqueness

`lineageTag` must be a **unique UUID per object across the entire model**. Every cloned or newly authored measure needs a fresh `uuid4` — **never reuse the donor's** `lineageTag`.

## The insertion anchor

Find the insertion point programmatically: in `_Measures.tmdl`, the line `\tpartition _Measures = m` occurs **exactly once** and marks the end of the measures. New measures insert immediately **before** it. (This is why the at-scale pipeline uses that anchor line as the `old_string` when appending chunks.)

## Paired structures that must stay in sync

Some objects span more than one place in the model. The tooling must keep them aligned:

- A `KPI`-style `SWITCH` measure must match its field-parameter table (`_PrmKPI`) **row-for-row** — every selectable measure has a corresponding field-parameter entry.
- **Calculated columns referenced by measures** (e.g., `DateWithSales`) live in the dimension TMDL files (e.g., `DimDate`), not in `_Measures.tmdl`. Dangling-reference scans must search all table files, not just the measure table.

## Related

- [Edit TMDL at Scale](../workflows/edit-tmdl-at-scale.md) — the generate → chunk → Edit → byte-verify pipeline that relies on this grammar
- [DAX Time-Intelligence Patterns](dax-time-intelligence-patterns.md) — the measure content authored into these blocks
- [examples/semantic_model.tmdl](../examples/semantic_model.tmdl) — a complete reference model in TMDL format

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

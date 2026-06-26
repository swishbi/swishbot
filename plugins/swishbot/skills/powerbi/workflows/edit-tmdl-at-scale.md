# Edit TMDL at Scale

## Purpose

Apply bulk changes to a Power BI semantic model's TMDL files — suites of 70–140 measures, documentation passes over thousands of measures, model-wide bug-fix rewrites — to a large `_Measures.tmdl` (37k+ lines, 1,900+ measures) with **zero corruption**.

This is the proven file-based procedure distilled from many rounds of production work. The headline rule: bulk TMDL changes are **never** hand-typed and **never** trusted to free-form edits. Everything flows through a `generate → chunk → Edit → byte-verify` pipeline where an independently-computed expected file is the source of truth.

Read [references/tmdl-anatomy.md](../references/tmdl-anatomy.md) first — this workflow assumes you understand TMDL block grammar, the UTF-8/CRLF encoding rule, `lineageTag` uniqueness, and the `partition _Measures = m` insertion anchor.

## When to use this vs. the Modeling MCP

The Power BI **Modeling MCP server is the preferred interactive path when it is available** — it creates, edits, and validates measures, relationships, columns, and calculation groups directly, with no whitespace bookkeeping. Reach for this file-based pipeline as the proven fallback when the Modeling MCP can't be used:

- **Cloud-synced PBIP paths** (OneDrive / SharePoint) where direct `Bash` writes to the model folder are sandbox-blocked.
- **No Windows / no Power BI Desktop** (headless, macOS-only, CI).
- **Very large mechanical changes** where you want a byte-exact audit trail and a clean rollback story per round.

## The pipeline: generate → chunk → Edit → byte-verify

1. **Backup.** Copy the target file to `$TMPDIR/<job>_backup/` before every round. Number the rounds — they are the rollback story.

2. **Write a Python generator** (commit it to the repo, run via `Bash`) that:
   - Parses measure blocks from the **current file bytes** — always `open(path, "rb").read().decode("utf-8")`, never text-mode `open()` (it silently translates CRLF→LF and breaks every `split("\r\n")` downstream). Header regex: `^\tmeasure (?:'([^']*)'|(\S+)) =`. Walk **back** over `\t///` lines to capture the measure's description; a block ends at the next block's first description line or at the partition anchor.
   - Builds the new/modified blocks (clone + rewrite — see the donor-clone procedure in [build-semantic-model.md](build-semantic-model.md)).
   - Emits three artifacts to `$TMPDIR`:
     - **(a) chunk files** of ~10 blocks each (the units you paste through the Edit tool),
     - **(b) a byte-exact `expected.tmdl`** — the *entire* file as it should exist after ALL planned edits,
     - **(c) an op manifest** for targeted edits — exact `old_string` / `new_string` pairs.

3. **Write a checker script** `check N` that re-derives the predicted file from *backup + chunks 1..N* and byte-compares it against the live file. Run it after every chunk.

4. **Apply chunks via the Edit tool** (the Edit tool — not `Bash` — is the write path; see the rules below). For each chunk: `old_string` = the partition anchor line (`\tpartition _Measures = m`), `new_string` = the chunk's block content followed by that same anchor line. Chunks land in order; new measures accumulate immediately above the partition. Run `check N` after each application. This step is mechanical and delegates cleanly to a subagent given explicit transcription rules.

5. **Apply targeted edits** from the op manifest (for in-place rewrites of existing measures). Use pairing for uniqueness (see below).

6. **Final verification = byte-diff against `expected.tmdl`**, plus the integrity sweep in the checklist below. The byte-diff is the authority: because `expected.tmdl` is computed *independently* of the application path, the two must agree byte-for-byte — any transcription slip anywhere in the pipeline (wrong whitespace, missed annotation, dangling ref) surfaces as the first diverging line.

## Edit-tool rules of engagement

These are the gotchas that cost real time. Design the pipeline around them from the start.

- **Bash writes to cloud-synced PBIP paths may be sandbox-blocked.** The Edit/Write tools are then the only write path: scripts generate content into `$TMPDIR`, and edits flow through the Edit tool into the model files.
- **`old_string` must match bytes exactly, including invisible whitespace.** There is no fuzzy matching. Power BI Desktop-formatted blank lines *inside* expressions come back as `\t\t\t` (tab-indented), not empty — transcribe them exactly.
- **The Edit tool strips trailing whitespace from every `new_string` line.** The generator must pre-`rstrip` every emitted line so `expected.tmdl` matches what the Edit tool actually writes.
- **`\n` in `old_string` matches CRLF files transparently**, and CRLF is preserved on write — you don't (and shouldn't) embed literal `\r\n` in match strings.
- **Achieve uniqueness via pairing.** When the target line isn't unique (e.g., `displayFolder: Leads` appears 11×, an `annotation` line appears 30×), pair it with the adjacent globally-unique `lineageTag` line or the measure's unique `///` description line to form the `old_string`.
- **`replace_all: true` only for genuinely identical repeated changes** (e.g., normalizing one `formatString` model-wide) — but **count occurrences first and assert the expected count** before applying.
- **`"File has been modified since read"`** happens whenever a subagent edited the file or Desktop/OneDrive re-saved it. Recover with a small windowed `Read` (10 lines anywhere in the file), then retry the same Edit.
- **Interruptions mid-batch are recoverable.** The `check N` script binary-searches which chunks already landed; resume from the first missing one.

## Verification checklist

Run after every round:

- [ ] Byte-diff vs generated `expected.tmdl` → identical
- [ ] Measure count == previous + added − removed (assert the exact number)
- [ ] Measure names unique; `lineageTag`s unique across the whole model
- [ ] Triple-backtick fence count is even
- [ ] Dangling-ref scan: every `[Name]` in new DAX resolves to a measure or column across **all** table TMDL files — don't forget measures defined outside `_Measures.tmdl` (e.g. `ShowValueForDates`, calculated columns like `DateWithSales`)
- [ ] CRLF intact, no stray lone CR or LF
- [ ] `displayFolder` counts per suite folder match (companions + base)
- [ ] Style sweep on new descriptions: end-user voice, no internal jargon (`int_`/surrogate/grain/seed)
- [ ] User spot-check in Desktop: one value variant, one % variant, one prior-period variant on a date-range card

## Related

- [references/tmdl-anatomy.md](../references/tmdl-anatomy.md) — TMDL file/block grammar, encoding, anchors, `lineageTag` rules
- [references/dax-time-intelligence-patterns.md](../references/dax-time-intelligence-patterns.md) — the DAX pattern library and format-mapping table the generator emits
- [build-semantic-model.md](build-semantic-model.md) — the donor-clone procedure for authoring new measure suites

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

# DAX Time-Intelligence Patterns

Battle-tested DAX patterns and the format-mapping rules used when authoring and cloning large time-intelligence (TI) measure suites. Pair this with the [donor-clone procedure](../workflows/build-semantic-model.md) (how to clone a suite) and [Edit TMDL at Scale](../workflows/edit-tmdl-at-scale.md) (how to apply the edits safely).

## Pattern library

### Prior-period day-for-day (PY / PQ / PM / PW)

Prior-period comparisons are **non-additive**. The correct approach:

1. Resolve the *latest period with data*: `CALCULATE( MAX( periodCol ), DateWithSales = TRUE )`.
2. Intersect the selected days via a `DaysSelected` `CALCULATETABLE`.
3. Shift with `periodCol = current − 1`.

```dax
KPI PM =
VAR PriorPeriod = CALCULATE( MAX( DimDate[Year Month No] ), DimDate[DateWithSales] = TRUE ) - 1
VAR DaysSelected = CALCULATETABLE( VALUES( DimDate[Day Of Period] ) )
RETURN
IF (
    [ShowValueForDates],
    CALCULATE( [KPI], DimDate[Year Month No] = PriorPeriod, DaysSelected )
)
```

**The anti-pattern that shipped once and cost an 86-measure rewrite** — the naive clone is *additive*, so multi-period selections become running totals:

```dax
// WRONG: SUMX over VALUES(periodCol) is additive across a multi-period selection
KPI PM (broken) =
SUMX( VALUES( DimDate[Year Month No] ),
      CALCULATE( [KPI], DimDate[Year Month No] = DimDate[Year Month No] - 1 ) )
```

### Sequential period-number columns in `dim_date`

`MAX(col) − 1` is only safe across year boundaries if the date dimension carries **monotonically increasing integer period columns** — e.g. `Year Month No = Year*12 + Month - 1`, `Year Quarter No = Year*4 + Quarter - 1`, `Year Week No`. **Mandate these columns in `dim_date`**; they are what make every prior-period shift correct at year rollover.

### Complete-prior-period (`*C`) measures

Do **not** guard `*C` measures with `HASONEVALUE` — it blanks the measure on any multi-period context (range slicers, grand totals). **`[ShowValueForDates]` alone is the guard.**

```dax
KPI PYC =
IF ( [ShowValueForDates], CALCULATE( [KPI], /* prior complete period filter */ ) )
```

### Highlight (conditional-format color) measures

Return a hex color by variance direction. Use `#1AAB40` (green) / `#D64550` (red):

```dax
KPI PoP Highlight =
VAR _v = [KPI PoP]
RETURN COALESCE( IF( _v >= 0, "#1AAB40" ), IF( _v < 0, "#D64550" ), "#000000" )
```

### Generic KPI suite

Write every TI variant **once** against `[KPI]` — the `SWITCH` measure over the `_PrmKPI` field parameter (see [build-semantic-model.md](../workflows/build-semantic-model.md#kpi-switcher-pattern)). Because the suite references `[KPI]` rather than a specific business measure, **selecting a different metric in `_PrmKPI` re-points the entire suite for free** — no per-metric DAX.

## Format mapping by base type

When cloning a suite onto a new base measure, map the `formatString` by the **base type**, and **assert-fail on any format you did not expect** (a surprise format is an inherited wart — see the donor audit rule in the build workflow):

| Base type | `formatString` | Format hint |
|-----------|----------------|-------------|
| Currency | `\$#,0.00;(\$#,0.00);\$#,0.00` | `PBI_FormatHint {"currencyCulture":"en-US"}` |
| Count | `#,0` | none — **drop the currency hint** when mapping currency → count |
| Rolling average | `#,0.00` | none |
| Percent (level) | `0.0%;-0.0%;0.0%` | none |
| Percent (Δ delta) | `#,0.0%;-#,0.0%;#,0.0%` | none |
| Highlight (color) | none | `isGeneralNumber`; triple-backtick fenced |

Percents are **1-decimal everywhere**: `0.0%;-0.0%;0.0%` for level measures and `#,0.0%;-#,0.0%;#,0.0%` for percentage deltas.

## Canonical TI suite catalog

A full TI suite is ~70–71 variants per base measure. The families:

| Family | Naming | What it computes | Format follows |
|--------|--------|------------------|----------------|
| `P*` | `PY`, `PQ`, `PM`, `PW` | Prior-period day-for-day (non-additive) | base type |
| `*o*` | `PoP`, `YoY`, `QoQ`, `MoM` (+ ` %`) | Period-over-period variance and % | base type / percent-Δ |
| `*TD` | `YTD`, `QTD`, `MTD`, `WTD` | To-date cumulative | base type |
| `PY*TD` | `PYTD`, `PYQTD`, … | Prior-year to-date | base type |
| `*TDoPY*TD` | `YTDoPYTD` (+ ` %`) | To-date vs prior-year-to-date variance and % | base type / percent-Δ |
| `*C` | `PYC`, `PQC`, … | Complete-prior-period (`[ShowValueForDates]` guard only) | base type |
| `Highlights` | `… Highlight` | Conditional-format color companion per variant | color (no formatString) |
| `AVG` | `AVG 1M`, `AVG Yesterday`, `AVG to Date` | Rolling averages / point comparisons | `#,0.00` |

Authoring conventions for the suite (so doc generation stays mechanical):

- Each base measure moves into its own suite display folder; companions live under `<Area>\<Base Name>`.
- Descriptions follow the template `"<Base> <variant phrase>."` so substitution is trivial — see the documentation style guide in [build-semantic-model.md](../workflows/build-semantic-model.md).
- **Think before cloning every variant**: a `(Reference Date)` variant that activates a `DimDate→DimJob` relationship double-filters against a base that already pins `DimDate→Fact` via `USERELATIONSHIP`. Drop variants whose semantics break for the base — don't clone for symmetry.

## Related

- [build-semantic-model.md](../workflows/build-semantic-model.md) — the donor-clone procedure that emits these measures
- [Edit TMDL at Scale](../workflows/edit-tmdl-at-scale.md) — applying suite edits to TMDL files safely
- [tmdl-anatomy.md](tmdl-anatomy.md) — block grammar, `lineageTag` rules, paired structures (`_PrmKPI`, `DateWithSales`)

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

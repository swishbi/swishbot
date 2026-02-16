# Create Logic Map

Translate documented tribal knowledge into column-level business logic and validate against the source system.

## Step 1: Translate to Staging References

Map each business concept to discrete staging table columns. This is the bridge between human language and data implementation.

- **Use explicit column references.** Not "the opportunity stage" but "from `stg_crm__opportunities.stage_name`." Every business concept must resolve to a specific table and column.
- **Document the transformation logic.** If a KPI requires combining fields, write it out: "Win rate = count of `stg_crm__opportunities` where `is_closed_won = true` / count of `stg_crm__opportunities` where `is_closed = true`."
- **Flag fields that do not exist yet.** If the business logic requires a derived field that is not in staging, document it as a gap. This becomes work for the intermediate or mart layer.
- **Maintain a mapping table.** For each KPI or business concept from requirements discovery, produce a row: business term → definition → source table(s) → source column(s) → transformation logic.

## Step 2: Validate Against Source

Compare your documented logic against the actual source system. Never trust documentation alone — verify against reality.

- **Pull a system-generated report.** Ask the SME to run their standard report from the source system UI. This is your ground truth.
- **Spot-check individual records.** Pick specific records from the report and trace them back through the data warehouse. Does the row in staging match what the SME sees on screen?
- **Test edge cases explicitly.** Take the exceptions from the SME interview and verify they are handled correctly. If "enterprise" requires three field conditions, find a record that meets two of three and confirm it is excluded.
- **Reconcile totals.** Compare aggregate numbers between the source system report and a query against staging. If they do not match, investigate — the gap is where undocumented business logic hides.

## Outputs

A completed business logic mapping produces three artifacts:

### Tribal Knowledge Documentation
- Process flows for each system (the end-to-end "soup to nuts" journey)
- Object and field catalog with relationships
- Business rules encoded in field combinations
- Valid values and their business meanings
- Exception cases and edge case handling

### Decision Log
- What was decided and by whom
- What was deferred and why
- Open questions that need resolution
- Assumptions made and their risk level

### Implementation-Ready Business Logic
- A mapping table: business term → definition → staging table → staging column(s) → transformation logic
- Each KPI from requirements discovery resolved to discrete column-level references
- Gaps identified (fields that need to be derived in intermediate or mart layers)
- Validation queries that can be used to verify correctness after implementation

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

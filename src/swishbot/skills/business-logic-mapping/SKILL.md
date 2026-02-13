---
name: business-logic-mapping
description: "Map tribal knowledge from subject matter experts into implementation-ready business logic tied to staging columns. Use after requirements discovery to bridge human understanding and SQL implementation."
---

# Business Logic Mapping

## Overview

You are acting as a business analyst working with subject matter experts (SMEs) — the power users and system administrators who live inside each operational system daily. These are not executives; these are the people who know which field combinations determine an opportunity type, why certain records get excluded from reports, and what the "real" process looks like versus what the documentation says.

This skill picks up after requirements discovery has identified the KPIs, segmentation, and source systems. Your job is to extract the tribal knowledge that lives in SMEs' heads and translate it into discrete, column-level business logic that an engineer (or Claude with dbt skills) can build against.

## Methodology

### 1. Identify SMEs

For each source system identified during requirements discovery (CRM, POS, ERP, HRIS, etc.), find the power user — the person who knows the system inside and out.

- **One system, one SME.** Each system should have a primary point of contact. If nobody owns the system knowledge, that is a risk to flag immediately.
- **Power users over administrators.** Admins know configuration; power users know how the business actually uses the system. You want the person who builds the reports, not the person who manages user permissions.
- **Document who knows what.** Create a simple map: system → SME → their role → what they own. This becomes your interview schedule.

### 2. Map Process Flows

Document the end-to-end business process within each system. Every system has a "soup to nuts" flow — lead-to-close, procure-to-pay, order-to-cash, hire-to-retire.

- **Walk through the process step by step.** Ask the SME to describe what happens from the moment a record enters the system to the moment it reaches its final state.
- **Identify decision points.** Where does the process branch? What determines which path a record takes? These decision points become your business logic.
- **Capture the exceptions.** The standard flow is easy. The value is in the edge cases: "Except when the customer is in segment X, then we skip step 3 and go straight to step 5."
- **Draw the flow, not the org chart.** Focus on how data moves through the system, not who is responsible for each step.

### 3. Document Objects & Fields

Catalog the system objects, their fields, and relationships. Focus on the fields that drive segmentation, business rules, and KPI calculations.

- **Start with the objects the SME uses daily.** In a CRM, that might be Accounts, Opportunities, and Activities. In an ERP, Sales Orders, Invoices, and Line Items.
- **Identify the fields that matter.** Not every field is relevant. Focus on fields used for filtering, grouping, calculating, and status tracking. Ask: "When you build a report, which fields do you filter or group by?"
- **Document field combinations that encode business rules.** A single field rarely tells the whole story. "An opportunity is considered 'enterprise' when `segment = 'Enterprise'` AND `annual_revenue > 1000000` AND `employee_count > 500`" — that logic lives nowhere except the SME's head.
- **Record valid values and their meanings.** Status fields, type fields, and category fields often have values whose meaning is not obvious from the label. "Status = 'D'" might mean "Deferred" in one system and "Deleted" in another.

### 4. Translate to Staging References

Map each business concept to discrete staging table columns. This is the bridge between human language and data implementation.

- **Use explicit column references.** Not "the opportunity stage" but "from `stg_crm__opportunities.stage_name`." Every business concept must resolve to a specific table and column.
- **Document the transformation logic.** If a KPI requires combining fields, write it out: "Win rate = count of `stg_crm__opportunities` where `is_closed_won = true` / count of `stg_crm__opportunities` where `is_closed = true`."
- **Flag fields that do not exist yet.** If the business logic requires a derived field that is not in staging, document it as a gap. This becomes work for the intermediate or mart layer.
- **Maintain a mapping table.** For each KPI or business concept from requirements discovery, produce a row: business term → definition → source table(s) → source column(s) → transformation logic.

### 5. Validate Against Source

Compare your documented logic against the actual source system. Never trust documentation alone — verify against reality.

- **Pull a system-generated report.** Ask the SME to run their standard report from the source system UI. This is your ground truth.
- **Spot-check individual records.** Pick specific records from the report and trace them back through the data warehouse. Does the row in staging match what the SME sees on screen?
- **Test edge cases explicitly.** Take the exceptions from step 2 and verify they are handled correctly. If "enterprise" requires three field conditions, find a record that meets two of three and confirm it is excluded.
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

## Anti-Patterns

- **Skipping SME conversations.** Documentation and data dictionaries are starting points, not substitutes. The business logic that matters most is the logic that is not written down anywhere.
- **Assuming field names are self-explanatory.** `status`, `type`, `category` — these mean different things in every system. Always ask: "What does this field represent and what are the valid values?"
- **Documenting at the wrong level of abstraction.** Too vague: "We calculate revenue from the CRM." Too implementation-heavy: "SELECT SUM(amount) FROM raw.crm.opportunities WHERE stage = 'Closed Won'." Just right: "Total revenue = sum of `stg_crm__opportunities.amount` where `stg_crm__opportunities.is_closed_won = true`, excluding opportunities where `stg_crm__opportunities.is_internal_test = true`."
- **Not validating against the source system.** If you have not compared your logic against what the SME sees on their screen, you have not validated. Data warehouse queries alone are not sufficient.
- **Treating this as a one-time exercise.** Business logic changes. SMEs leave. Document enough that someone new can understand the logic without the original SME in the room.

## Related Skills

- **[requirements-discovery](../requirements-discovery/SKILL.md)** — Upstream: produces the KPIs, segmentation, and source systems that this skill maps to implementation logic
- **[dbt-staging](../dbt-staging/SKILL.md)** — The staging models whose columns are referenced in business logic mappings
- **[dbt-intermediate](../dbt-intermediate/SKILL.md)** — Downstream: consumes business logic to build cross-system transformations
- **[dbt-marts](../dbt-marts/SKILL.md)** — Downstream: produces the final outputs that implement the mapped KPIs
- **[dimensional-modeling](../dimensional-modeling/SKILL.md)** — Fact and dimension design informed by the documented business rules and relationships

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

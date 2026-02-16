---
name: business-logic-mapping
description: "Map tribal knowledge from subject matter experts into implementation-ready business logic tied to staging columns. Use after requirements discovery to bridge human understanding and SQL implementation."
workflows:
  - name: run-sme-interview
    trigger: "When you need to extract tribal knowledge from subject matter experts"
  - name: create-logic-map
    trigger: "When documented knowledge needs to be translated into column-level business logic"
---

# Business Logic Mapping

## Overview

You are acting as a business analyst working with subject matter experts (SMEs) — the power users and system administrators who live inside each operational system daily. These are not executives; these are the people who know which field combinations determine an opportunity type, why certain records get excluded from reports, and what the "real" process looks like versus what the documentation says.

This skill picks up after requirements discovery has identified the KPIs, segmentation, and source systems. Your job is to extract the tribal knowledge that lives in SMEs' heads and translate it into discrete, column-level business logic that an engineer (or Claude with dbt skills) can build against.

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Run SME Interview](workflows/run-sme-interview.md) | Extract tribal knowledge — identify SMEs, map process flows, document objects and fields |
| [Create Logic Map](workflows/create-logic-map.md) | Translate knowledge into column-level staging references and validate against source |

**Full mapping workflow:** For a new source system, run both workflows in order.

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

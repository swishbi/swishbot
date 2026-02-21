---
name: requirements-discovery
description: "Act as a business analyst to guide stakeholders from idea to implementation-ready requirements. Use when a user asks to scope a report, run a discovery session, gather requirements for a dashboard, produce a developer specification, interview SMEs, extract business rules, document column-level logic, or map business logic to staging columns."
argument-hint: "[deliverable]"
---

# Requirements Discovery

## Overview

You are acting as a business analyst. Your role is to guide a stakeholder from a vague idea — "I need a report," "can we track X?" — to a concrete, implementation-ready specification that an engineer can build against.

The stakeholder provides the **what** and **why**. You provide the **how** — through structured questioning, scope narrowing, and reverse engineering the technical requirements from the desired outcome.

This is phase 0. No code gets written, no models get built, until discovery is complete.

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Run Discovery Session](workflows/run-discovery-session.md) | Stakeholder brings a vague idea — guide them through scoping |
| [Produce Developer Requirements](workflows/produce-developer-requirements.md) | Scoped deliverable needs a technical specification for engineers |
| [Run SME Interview](workflows/run-sme-interview.md) | Interview SMEs and map source system objects and fields |
| [Create Logic Map](workflows/create-logic-map.md) | Translate tribal knowledge to column-level staging logic |

**Full BA workflow:** For a new request, run all four workflows in order.

## Anti-Patterns

- **Letting the stakeholder dictate the how.** The stakeholder owns the problem. You own the solution. "I need a stored procedure that runs at 6am" is a solution, not a requirement. Dig for the underlying need.
- **Boiling the ocean.** A request that touches every part of the business is not one project. Break it down ruthlessly. Ship the first piece, learn, iterate.
- **Mistaking process problems for technology problems.** "The data is wrong" often means "nobody owns data quality in this process." A new pipeline will not fix a broken process.
- **Skipping straight to building.** The temptation to start coding is strong. Resist it. Thirty minutes of discovery saves days of rework.
- **Gold-plating the spec.** The spec should be precise enough to build against, not so detailed that it takes longer to write than to build. Focus on decisions, not documentation.
- **Skipping SME conversations.** Documentation and data dictionaries are starting points, not substitutes. The business logic that matters most is the logic that is not written down anywhere.
- **Assuming field names are self-explanatory.** `status`, `type`, `category` — these mean different things in every system. Always ask: "What does this field represent and what are the valid values?"
- **Not validating against the source system.** If you have not compared your logic against what the SME sees on their screen, you have not validated. Data warehouse queries alone are not sufficient.

## Related Skills

- **[dbt](../dbt/SKILL.md)** — The staging, intermediate, and mart models whose columns are referenced in business logic mappings
- **[dimensional-modeling](../dimensional-modeling/SKILL.md)** — Fact and dimension design informed by the documented business rules and relationships

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

---
name: dimensional-modeling
description: "Apply dimensional modeling best practices. Use when a user asks to design a star schema, choose grain for a fact table, handle slowly changing dimensions, conform dimensions across sources, or structure a bus matrix."
argument-hint: "[business-process]"
---

# Dimensional Modeling

## Overview

Dimensional modeling follows the Kimball methodology as its foundation: star schemas, conformed dimensions, the bus matrix, and a relentless focus on grain. This skill encodes the *design* layer — the decisions about what to model and why — while **dbt** handles the *implementation* layer of how models are built.

Modern adaptations from the traditional Kimball approach:

- **Hash surrogate keys** — deterministic, reproducible keys via `dbt_utils.generate_surrogate_key` instead of auto-incrementing integers
- **Cloud-native materialization** — table/incremental strategies in cloud warehouses where storage is cheap and compute is the bottleneck
- **dbt as the implementation layer** — the DAG enforces lineage, testing, and documentation that Kimball originally solved with ETL tooling
- **Lightweight cross-system conformance** — borrowing the "same-as link" concept from Data Vault 2.0 without the full hub/link/satellite object explosion

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Design Star Schema](workflows/design-star-schema.md) | Designing new facts and dimensions — grain, keys, SCD, unknown members |
| [Conform Cross-System Data](workflows/conform-cross-system-data.md) | Same entity in multiple systems — matching, cross-references, survivorship |

## Patterns

Each pattern has a corresponding example file in the [examples/](examples/) directory.

| Pattern | Example File | Description |
|---------|-------------|-------------|
| Single-source dimension | [dim_single_source.sql](examples/dim_single_source.sql) | Hash surrogate key, unknown member via macro, `dbt_utils.star()`, `hash_diff` |
| Single-source fact | [fct_single_source.sql](examples/fct_single_source.sql) | Surrogate FKs to dimensions, unknown member coalesce |
| Cross-system entity cross-reference | [int_cross_reference.sql](examples/int_cross_reference.sql) | System foreign key matching with matched/anchor-only/secondary-only handling |
| Conformed dimension | [dim_conformed.sql](examples/dim_conformed.sql) | Multiple sources with survivorship rules and linkage status flag |
| Unknown member macro | [add_unknown_member_row.sql](examples/add_unknown_member_row.sql) | Column-introspecting macro with configurable label |
| Business key cross-reference | See [conform-cross-system-data](workflows/conform-cross-system-data.md) workflow | Fallback when no system cross-reference exists |

## Anti-Patterns

- **Auto-incrementing surrogate keys** — Non-deterministic, breaks idempotency on full refresh, produces different keys across environments. Use hash-based keys.
- **Skipping grain declaration** — If you cannot state the grain in one sentence, stop and clarify before writing any SQL.
- **Building SCD2 dimensions without a business requirement** — SCD2 adds complexity to every downstream join. Default to SCD1 and only add history when explicitly needed.
- **Snowflaking dimensions for normalization's sake** — Storage is cheap. A denormalized `dim_products` with category and subcategory columns is better than `dim_products` → `dim_categories` → `dim_subcategories`.
- **Creating DV2-style hubs/links/satellites when a cross-reference model suffices** — The full Data Vault 2.0 pattern introduces significant object sprawl. A single cross-reference intermediate model achieves the same conformance goal for most use cases.
- **Conforming by name-matching without a verified key** — Matching on `customer_name` alone will produce false positives. Use the matching hierarchy: system cross-references first, verified business keys second.
- **Treating system cross-references as permanent** — System foreign keys (`erp.crm_customer_id`) are pragmatically reliable but represent integration debt. Document them, use them, and advocate for true business keys over time.
- **NULL foreign keys in fact tables** — Never allow a NULL dimension key on a fact row. Coalesce to the unknown member key so gaps are explicit and queryable, not silently invisible.
- **Mixing design and implementation concerns** — This skill defines *what* to model. Use dbt for *how* to implement it.

## Related Skills

- **[requirements-discovery](../requirements-discovery/SKILL.md)** — Upstream discovery process that identifies which facts and dimensions need to be modeled
- **[dbt](../dbt/SKILL.md)** — The transformation layer that implements the dimensional models designed here
- **[powerbi](../powerbi/SKILL.md)** — Power BI semantic models that consume the star schemas designed here

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

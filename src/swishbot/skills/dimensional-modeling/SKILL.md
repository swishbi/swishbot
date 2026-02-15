---
name: dimensional-modeling
description: "Apply dimensional modeling best practices. Use when designing fact and dimension tables, choosing grain, handling slowly changing dimensions, or structuring a star/snowflake schema."
---

# Dimensional Modeling

## Overview

Dimensional modeling follows the Kimball methodology as its foundation: star schemas, conformed dimensions, the bus matrix, and a relentless focus on grain. This skill encodes the *design* layer — the decisions about what to model and why — while **dbt-intermediate** and **dbt-marts** handle the *implementation* layer of how models are built.

Modern adaptations from the traditional Kimball approach:

- **Hash surrogate keys** — deterministic, reproducible keys via `dbt_utils.generate_surrogate_key` instead of auto-incrementing integers
- **Cloud-native materialization** — table/incremental strategies in cloud warehouses where storage is cheap and compute is the bottleneck
- **dbt as the implementation layer** — the DAG enforces lineage, testing, and documentation that Kimball originally solved with ETL tooling
- **Lightweight cross-system conformance** — borrowing the "same-as link" concept from Data Vault 2.0 without the full hub/link/satellite object explosion

## Core Concepts

### Grain

Always declare grain first — everything else follows from it. The grain is the single most important decision in dimensional modeling. It defines what one row in a fact or dimension table represents.

Ask: *"What does one row in this table mean?"* If you cannot answer in a single sentence, the grain is not clear enough.

- **Transaction grain** — one row per event (one order, one payment, one click)
- **Periodic snapshot grain** — one row per entity per time period (one account per month)
- **Accumulating snapshot grain** — one row per process instance, updated as milestones are reached (one order from placement through delivery)

### Surrogate Keys

Use deterministic hash-based surrogate keys. They are reproducible across full-refresh and incremental runs, and they work identically across environments.

**Single-source entity:**
```sql
{{ dbt_utils.generate_surrogate_key(['order_id']) }}
```

**SCD2 source (where the ingestion tool captures history):**
```sql
{{ dbt_utils.generate_surrogate_key(['customer_id', 'valid_from']) }}
```

**Multi-source conformed entity:**
```sql
-- Use the conformed business key, not the source system key
{{ dbt_utils.generate_surrogate_key(['conformed_customer_id']) }}
```

Why not auto-incrementing integers:
- Non-deterministic — a full refresh produces different keys
- Breaks idempotency — incremental runs cannot reproduce the same key for the same record
- Environment-dependent — dev and prod generate different keys for the same data

### SCD Handling

Ingestion tools (dlt, Fivetran, Airbyte) may capture SCD2 history at the source level. However, transformed dimension models should **default to SCD1** (current state only) unless there is an explicit business requirement for historical tracking.

**Default approach — SCD1:**
```sql
-- Filter to current record from SCD2 source
where valid_to is null
```

**When to use SCD2 in dimensions:**
- The business explicitly needs to answer "what was the value at that point in time?"
- Regulatory or audit requirements mandate historical tracking
- A fact table needs to join to the dimension *as of* the transaction date

### Fact Tables

| Type | Grain | Update Pattern | Example |
|------|-------|----------------|---------|
| Transaction | One row per event | Insert-only | Orders, payments, clicks |
| Periodic snapshot | One row per entity per period | Insert per period | Monthly account balances |
| Accumulating snapshot | One row per process instance | Update as milestones occur | Order lifecycle (placed → shipped → delivered) |

### Dimension Tables

| Type | Description | When to Use |
|------|-------------|-------------|
| Conformed | Shared across multiple facts and business areas | Any entity referenced by 2+ fact tables (customer, product, date) |
| Role-playing | Same dimension joined multiple times with different meanings | Date dimension as `order_date`, `ship_date`, `delivery_date` |
| Junk | Collects low-cardinality flags and indicators into one table | Status flags, boolean indicators, type codes that do not warrant their own dimension |
| Degenerate | Dimension key with no associated dimension table — lives on the fact | Transaction number, invoice number, order number |

### Unknown Member Rows

Every dimension should include an **unknown member row** — a single record that represents "we don't know." When a fact record cannot find a matching dimension (the left join produces a NULL foreign key), the fact should point to the unknown member instead.

This is a core Kimball principle: **fact tables should never have NULL foreign keys.** NULLs break aggregations, complicate BI tool filters, and force every downstream query to handle missing data. An explicit unknown row makes the gap visible and queryable.

**The `add_unknown_member_row` macro:**

Rather than hand-coding an unknown row per dimension (fragile, must be updated when columns change), use a macro that introspects the dimension's columns and generates the row automatically. The macro accepts a configurable label so teams can choose what text appears for missing data (`'*Unknown*'`, `'CHECK'`, `'N/A'`, etc.). See [examples/add_unknown_member_row.sql](examples/add_unknown_member_row.sql) for the full macro.

How it works:

- **String columns** (varchar, text, etc.) get the configurable `unknown_label` — this is what shows up in BI tools
- **Integer columns** get `-1` — a classic Kimball sentinel that is clearly not real data
- **Float/decimal columns** get `null` — no meaningful sentinel for continuous values
- **Boolean columns** get `false`
- **Date/timestamp columns** get `null`
- The unknown row is unioned *before* the real data so it appears first for easy visual confirmation

**Configuring the label:**

Set the default label as a dbt project variable so every dimension uses the same value, overridable per-model if needed:

```yaml
# dbt_project.yml
vars:
  unknown_member_label: '*Unknown*'  # or 'CHECK', 'N/A', etc.
```

**Using the macro in a dimension model:**

Call the macro inside the **source CTE** so the unknown row enters early and flows through all downstream transformations — surrogate key generation, `dbt_utils.star()`, `hash_diff`, etc. — without special handling. Because `adapter.get_columns_in_relation` needs to query the warehouse schema, the macro call must be in a CTE that references a materialized relation (a staging model), not an ephemeral CTE defined earlier in the same model. See [examples/dim_single_source.sql](examples/dim_single_source.sql) for the full pattern.

How this works:

1. The `add_unknown_member_row` macro generates a `select` with one unknown row `union all select * from ref(...)` — this becomes the source CTE
2. `dbt_utils.star()` dynamically lists all columns from the staging relation, keeping the model DRY
3. `dbt_utils.generate_surrogate_key(column_names)` produces a `hash_diff` for change detection — the unknown row gets its own deterministic hash
4. The surrogate key for the unknown row is produced by the same `dbt_utils.generate_surrogate_key` expression as every other row; for the unknown, the macro supplies default natural-key values (for example, the `unknown_label` for string keys and `-1` for numeric keys), so the hash is deterministic and reproducible
5. The `where valid_to is null` filter passes the unknown row through because the macro sets date columns to `null`

> **Important:** The macro introspects columns via `adapter.get_columns_in_relation`, which requires the target relation to already exist in the warehouse. On a fresh `dbt run` against an empty schema, the first run materializes without the unknown row. The second run picks it up. This is acceptable for initial deployment — the unknown row is a quality feature, not a structural dependency.

**Coalescing in the fact table:**

Fact tables replace NULL dimension keys with the unknown member's surrogate key so NULLs never propagate. See [examples/fct_single_source.sql](examples/fct_single_source.sql) for the full pattern. The coalesce must reuse the same natural-key expression (including default values such as `-1` or the `unknown_member_label`) that the dimension uses to compute the unknown-member hash:

```sql
coalesce(
    customers.customer_key,
    {{ dbt_utils.generate_surrogate_key([
        "coalesce(customers.customer_natural_key, -1)"
    ]) }}
) as customer_key
```

**Guidelines:**

- Set `unknown_member_label` once in `dbt_project.yml` — all dimensions and facts reference the same variable
- The macro should live in the project's `macros/` directory, not inside a specific model
- Call the macro in the **source CTE**, not around the final select — it must reference a materialized relation for schema introspection to work
- On first deployment to an empty schema, the unknown row will not appear until the second run (adapter introspection requires an existing relation)
- When a fact row points to the unknown member, that is a **data quality signal** — monitor the count of unknown-member joins as a metric
- Add a dbt test asserting each dimension has exactly one row where the natural key equals the `unknown_member_label`

## Conforming Data Across Source Systems

This is the most challenging part of dimensional modeling in practice. When the same business entity (customer, product, employee) exists in multiple source systems, you need a strategy to produce one conformed dimension.

Kimball prescribes conforming on **natural business keys** — identifiers meaningful to the business like email, tax ID, or SKU. In practice, true business keys are often inconsistent, incomplete, or simply not shared across systems. What you *do* find reliably is **system cross-references**: one system stores the foreign key of another (e.g., the ERP has a `crm_customer_id` column because an integration syncs it). These system-level foreign keys are the most dependable link you have, even though they are technically source-system artifacts rather than business keys.

This creates a tension with Kimball's guidance to avoid dependency on source system keys. The pragmatic resolution: **use what is reliable now, document the debt, and push for true business keys over time.** A conformed dimension built on a verified system cross-reference is far more valuable than no conformed dimension at all.

### Matching Hierarchy

When conforming an entity across systems, evaluate matching strategies in this order:

| Priority | Strategy | Reliability | Example |
|----------|----------|-------------|---------|
| 1 | **System cross-references** | Highest — maintained by integrations | ERP stores `crm_customer_id` from CRM |
| 2 | **Verified business keys** | High — if consistently populated | Email address present and validated in both systems |
| 3 | **Composite business keys** | Medium — multiple weak keys combined | Name + postal code + phone number |
| 4 | **Fuzzy / probabilistic matching** | Low — requires external tooling | Name similarity + address normalization |

In most real-world projects, **priority 1 is what you actually have**. Do not spend weeks pursuing a pure business key strategy when a system cross-reference already exists and is reliable.

### System Cross-Reference Pattern

The most common scenario: System B stores a reference to System A's identifier. This is the pattern you will use most often. See [examples/int_cross_reference.sql](examples/int_cross_reference.sql) for the full implementation.

Key decisions in this pattern:

- **Anchor to the most authoritative system** — CRM owns the customer entity, so `crm_customer_id` drives the surrogate key for matched records. ERP-only records get a key derived from `erp_customer_id` until they are linked.
- **Surface the gaps** — ERP records with a null `crm_customer_id` are *unlinked* records. Surfacing them explicitly enables data quality monitoring and gives the business a queue to work through.
- **Do not silently drop unmatched records** — Use `union all` to keep all records from all systems. Orphans are a data quality issue to fix, not rows to discard.

### Business Key Cross-Reference Pattern

When no system cross-reference exists but a reliable business key is shared across systems, fall back to matching on the business key directly:

```sql
-- int_customers_cross_referenced.sql
-- No system cross-reference available — matching on verified email

with

crm_customers as (
    select * from {{ ref('stg_crm__customers') }}
),

billing_customers as (
    select * from {{ ref('stg_billing__customers') }}
),

cross_referenced as (
    select
        coalesce(crm.email, billing.email) as conformed_email,
        crm.crm_customer_id,
        billing.billing_customer_id,
        {{ dbt_utils.generate_surrogate_key(['coalesce(crm.email, billing.email)']) }} as customer_key
    from crm_customers as crm
    full outer join billing_customers as billing
        on lower(trim(crm.email)) = lower(trim(billing.email))
)

select * from cross_referenced
```

When relying on business keys, always:
- **Normalize before matching** — `lower(trim(...))` at minimum; consider stripping whitespace, punctuation
- **Test match rates** — add a dbt test or exposure that reports the percentage of records that match vs. remain orphaned
- **Document the fragility** — business key matching will break when data entry is inconsistent

### Choosing the Anchor System

When multiple systems contain the same entity, one system must be the **anchor** — the authoritative source whose key drives the conformed surrogate key:

- The anchor is the system where the entity is *created and managed* (CRM for customers, ERP for products, HRIS for employees)
- Records from the anchor system always get a surrogate key, even if they have no match in secondary systems
- Records from secondary systems that cannot be linked get a surrogate key derived from their own system key — these are flagged as unlinked for data quality follow-up

### Conformed Dimension Pattern

Once the cross-reference establishes identity, build the conformed dimension by coalescing attributes from multiple sources with explicit **survivorship rules**. See [examples/dim_conformed.sql](examples/dim_conformed.sql) for the full implementation including the `linkage_status` flag for data quality monitoring.

### Survivorship Rules

When the same attribute exists in multiple sources, define which source wins. Common strategies:

| Strategy | Rule | When to Use |
|----------|------|-------------|
| Priority-based | Source A always wins over Source B | One system is the authoritative master for that attribute |
| Most recent | Latest `updated_at` wins | No single master, freshest data is best |
| Most complete | Non-null value wins, prefer longer strings | Filling gaps from secondary sources |
| Business-defined | Specific logic per attribute | Mixed rules across attributes |

Document survivorship rules in the model's YAML description and in the cross-reference model's SQL comments. These are business decisions, not technical ones — they should be reviewed with stakeholders during requirements discovery.

### Data Quality and Linkage Monitoring

Conformance is not a one-time activity. Add monitoring to track linkage health:

- **Match rate** — what percentage of secondary-system records link to the anchor system? A declining match rate signals an integration or data entry problem.
- **Orphan queue** — surface unlinked records (`linkage_status != 'linked'`) to a dashboard or report that the business can act on.
- **Duplicate detection** — multiple anchor records matching a single secondary record indicates a deduplication problem upstream.

### Fuzzy Matching

When deterministic matching (system cross-references or business keys) is not sufficient (e.g., name-only matching, address normalization), this is **not a dbt concern**. Fuzzy matching and entity resolution belong in:

- A dedicated MDM (Master Data Management) tool
- A preprocessing step before data enters the warehouse
- A separate pipeline that produces a verified cross-reference table that dbt can consume

The dbt cross-reference model should consume the output of entity resolution, not attempt to perform it.

## Patterns

Each pattern has a corresponding example file in the [examples/](examples/) directory.

| Pattern | Example File | Description |
|---------|-------------|-------------|
| Single-source dimension | [dim_single_source.sql](examples/dim_single_source.sql) | Hash surrogate key, unknown member via macro, `dbt_utils.star()`, `hash_diff` |
| Single-source fact | [fct_single_source.sql](examples/fct_single_source.sql) | Surrogate FKs to dimensions, unknown member coalesce |
| Cross-system entity cross-reference | [int_cross_reference.sql](examples/int_cross_reference.sql) | System foreign key matching with matched/anchor-only/secondary-only handling |
| Conformed dimension | [dim_conformed.sql](examples/dim_conformed.sql) | Multiple sources with survivorship rules and linkage status flag |
| Unknown member macro | [add_unknown_member_row.sql](examples/add_unknown_member_row.sql) | Column-introspecting macro with configurable label |
| Business key cross-reference | See [Business Key Cross-Reference Pattern](#business-key-cross-reference-pattern) above | Fallback when no system cross-reference exists |

## Anti-Patterns

- **Auto-incrementing surrogate keys** — Non-deterministic, breaks idempotency on full refresh, produces different keys across environments. Use hash-based keys.
- **Skipping grain declaration** — If you cannot state the grain in one sentence, stop and clarify before writing any SQL.
- **Building SCD2 dimensions without a business requirement** — SCD2 adds complexity to every downstream join. Default to SCD1 and only add history when explicitly needed.
- **Snowflaking dimensions for normalization's sake** — Storage is cheap. A denormalized `dim_products` with category and subcategory columns is better than `dim_products` → `dim_categories` → `dim_subcategories`.
- **Creating DV2-style hubs/links/satellites when a cross-reference model suffices** — The full Data Vault 2.0 pattern introduces significant object sprawl. A single cross-reference intermediate model achieves the same conformance goal for most use cases.
- **Conforming by name-matching without a verified key** — Matching on `customer_name` alone will produce false positives. Use the matching hierarchy: system cross-references first, verified business keys second.
- **Treating system cross-references as permanent** — System foreign keys (`erp.crm_customer_id`) are pragmatically reliable but represent integration debt. Document them, use them, and advocate for true business keys over time.
- **NULL foreign keys in fact tables** — Never allow a NULL dimension key on a fact row. Coalesce to the unknown member key so gaps are explicit and queryable, not silently invisible.
- **Mixing design and implementation concerns** — This skill defines *what* to model. Use dbt-intermediate and dbt-marts for *how* to implement it.

## Related Skills

- **[requirements-discovery](../requirements-discovery/SKILL.md)** — Upstream discovery process that identifies which facts and dimensions need to be modeled
- **[business-logic-mapping](../business-logic-mapping/SKILL.md)** — Maps business rules and survivorship logic that feed into dimension and fact definitions
- **[dbt-staging](../dbt-staging/SKILL.md)** — The first transformation layer that produces clean inputs for dimensional models
- **[dbt-intermediate](../dbt-intermediate/SKILL.md)** — Where cross-reference models and grain-changing transformations live
- **[dbt-marts](../dbt-marts/SKILL.md)** — Where final fact and dimension tables are materialized
- **[dbt-style](../dbt-style/SKILL.md)** — Naming, SQL style, and project structure conventions applied to dimensional models

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

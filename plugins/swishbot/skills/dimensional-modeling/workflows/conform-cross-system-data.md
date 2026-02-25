# Conform Cross-System Data

Establish identity across source systems using cross-references, survivorship rules, and conformed dimensions.

## Step 1: Evaluate Matching Strategy

When the same business entity (customer, product, employee) exists in multiple source systems, evaluate matching strategies in this order:

| Priority | Strategy | Reliability | Example |
|----------|----------|-------------|---------|
| 1 | **System cross-references** | Highest — maintained by integrations | ERP stores `crm_customer_id` from CRM |
| 2 | **Verified business keys** | High — if consistently populated | Email address present and validated in both systems |
| 3 | **Composite business keys** | Medium — multiple weak keys combined | Name + postal code + phone number |
| 4 | **Fuzzy / probabilistic matching** | Low — requires external tooling | Name similarity + address normalization |

In most real-world projects, **priority 1 is what you actually have**. Do not spend weeks pursuing a pure business key strategy when a system cross-reference already exists and is reliable.

## Step 2: Build System Cross-Reference

The most common scenario: System B stores a reference to System A's identifier. This is the pattern you will use most often. See [examples/int_cross_reference.sql](../examples/int_cross_reference.sql) for the full implementation.

Key decisions in this pattern:

- **Anchor to the most authoritative system** — CRM owns the customer entity, so `crm_customer_id` drives the surrogate key for matched records. ERP-only records get a key derived from `erp_customer_id` until they are linked.
- **Surface the gaps** — ERP records with a null `crm_customer_id` are *unlinked* records. Surfacing them explicitly enables data quality monitoring and gives the business a queue to work through.
- **Do not silently drop unmatched records** — Use `union all` to keep all records from all systems. Orphans are a data quality issue to fix, not rows to discard.

### Business Key Cross-Reference (Fallback)

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

## Step 3: Choose the Anchor System

When multiple systems contain the same entity, one system must be the **anchor** — the authoritative source whose key drives the conformed surrogate key:

- The anchor is the system where the entity is *created and managed* (CRM for customers, ERP for products, HRIS for employees)
- Records from the anchor system always get a surrogate key, even if they have no match in secondary systems
- Records from secondary systems that cannot be linked get a surrogate key derived from their own system key — these are flagged as unlinked for data quality follow-up

## Step 4: Build Conformed Dimension

Once the cross-reference establishes identity, build the conformed dimension by coalescing attributes from multiple sources with explicit **survivorship rules**. See [examples/dim_conformed.sql](../examples/dim_conformed.sql) for the full implementation including the `linkage_status` flag for data quality monitoring.

### Survivorship Rules

When the same attribute exists in multiple sources, define which source wins. Common strategies:

| Strategy | Rule | When to Use |
|----------|------|-------------|
| Priority-based | Source A always wins over Source B | One system is the authoritative master for that attribute |
| Most recent | Latest `updated_at` wins | No single master, freshest data is best |
| Most complete | Non-null value wins, prefer longer strings | Filling gaps from secondary sources |
| Business-defined | Specific logic per attribute | Mixed rules across attributes |

Document survivorship rules in the model's YAML description and in the cross-reference model's SQL comments. These are business decisions, not technical ones — they should be reviewed with stakeholders during requirements discovery.

## Step 5: Monitor Linkage Health

Conformance is not a one-time activity. Add monitoring to track linkage health:

- **Match rate** — what percentage of secondary-system records link to the anchor system? A declining match rate signals an integration or data entry problem.
- **Orphan queue** — surface unlinked records (`linkage_status != 'linked'`) to a dashboard or report that the business can act on.
- **Duplicate detection** — multiple anchor records matching a single secondary record indicates a deduplication problem upstream.

## Fuzzy Matching

When deterministic matching (system cross-references or business keys) is not sufficient (e.g., name-only matching, address normalization), this is **not a dbt concern**. Fuzzy matching and entity resolution belong in:

- A dedicated MDM (Master Data Management) tool
- A preprocessing step before data enters the warehouse
- A separate pipeline that produces a verified cross-reference table that dbt can consume

The dbt cross-reference model should consume the output of entity resolution, not attempt to perform it.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

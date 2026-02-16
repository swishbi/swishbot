# Design Star Schema

Design fact tables, dimension tables, grain, surrogate keys, SCD handling, and unknown member rows.

## Step 1: Declare Grain

Always declare grain first — everything else follows from it. The grain is the single most important decision in dimensional modeling. It defines what one row in a fact or dimension table represents.

Ask: *"What does one row in this table mean?"* If you cannot answer in a single sentence, the grain is not clear enough.

- **Transaction grain** — one row per event (one order, one payment, one click)
- **Periodic snapshot grain** — one row per entity per time period (one account per month)
- **Accumulating snapshot grain** — one row per process instance, updated as milestones are reached (one order from placement through delivery)

## Step 2: Choose Surrogate Keys

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

## Step 3: Handle SCD

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

## Step 4: Design Fact Tables

| Type | Grain | Update Pattern | Example |
|------|-------|----------------|---------|
| Transaction | One row per event | Insert-only | Orders, payments, clicks |
| Periodic snapshot | One row per entity per period | Insert per period | Monthly account balances |
| Accumulating snapshot | One row per process instance | Update as milestones occur | Order lifecycle (placed → shipped → delivered) |

## Step 5: Design Dimension Tables

| Type | Description | When to Use |
|------|-------------|-------------|
| Conformed | Shared across multiple facts and business areas | Any entity referenced by 2+ fact tables (customer, product, date) |
| Role-playing | Same dimension joined multiple times with different meanings | Date dimension as `order_date`, `ship_date`, `delivery_date` |
| Junk | Collects low-cardinality flags and indicators into one table | Status flags, boolean indicators, type codes that do not warrant their own dimension |
| Degenerate | Dimension key with no associated dimension table — lives on the fact | Transaction number, invoice number, order number |

## Step 6: Add Unknown Member Rows

Every dimension should include an **unknown member row** — a single record that represents "we don't know." When a fact record cannot find a matching dimension (the left join produces a NULL foreign key), the fact should point to the unknown member instead.

This is a core Kimball principle: **fact tables should never have NULL foreign keys.** NULLs break aggregations, complicate BI tool filters, and force every downstream query to handle missing data. An explicit unknown row makes the gap visible and queryable.

**The `add_unknown_member_row` macro:**

Rather than hand-coding an unknown row per dimension (fragile, must be updated when columns change), use a macro that introspects the dimension's columns and generates the row automatically. The macro accepts a configurable label so teams can choose what text appears for missing data (`'*Unknown*'`, `'CHECK'`, `'N/A'`, etc.). See [examples/add_unknown_member_row.sql](../examples/add_unknown_member_row.sql) for the full macro.

How it works:

- **String columns** (varchar, text, etc.) get the configurable `unknown_label` — this is what shows up in BI tools
- **Integer columns** get `-1` — a classic Kimball sentinel that is clearly not real data
- **Float/decimal columns** get `null` — no meaningful sentinel for continuous values
- **Boolean columns** get `false`
- **Date/timestamp columns** get `null`
- The unknown row is unioned *before* the real data so it appears first for easy visual confirmation

**Configuring the label:**

```yaml
# dbt_project.yml
vars:
  unknown_member_label: '*Unknown*'  # or 'CHECK', 'N/A', etc.
```

**Using the macro in a dimension model:**

Call the macro inside the **source CTE** so the unknown row enters early and flows through all downstream transformations — surrogate key generation, `dbt_utils.star()`, `hash_diff`, etc. — without special handling. Because `adapter.get_columns_in_relation` needs to query the warehouse schema, the macro call must be in a CTE that references a materialized relation (a staging model), not an ephemeral CTE defined earlier in the same model. See [examples/dim_single_source.sql](../examples/dim_single_source.sql) for the full pattern.

How this works:

1. The `add_unknown_member_row` macro generates a `select` with one unknown row `union all select * from ref(...)` — this becomes the source CTE
2. `dbt_utils.star()` dynamically lists all columns from the staging relation, keeping the model DRY
3. `dbt_utils.generate_surrogate_key(column_names)` produces a `hash_diff` for change detection — the unknown row gets its own deterministic hash
4. The surrogate key for the unknown row is produced by the same `dbt_utils.generate_surrogate_key` expression as every other row; for the unknown, the macro supplies default natural-key values (for example, the `unknown_label` for string keys and `-1` for numeric keys), so the hash is deterministic and reproducible
5. The `where valid_to is null` filter passes the unknown row through because the macro sets date columns to `null`

> **Important:** The macro introspects columns via `adapter.get_columns_in_relation`, which requires the target relation to already exist in the warehouse. On a fresh `dbt run` against an empty schema, the first run materializes without the unknown row. The second run picks it up. This is acceptable for initial deployment — the unknown row is a quality feature, not a structural dependency.

**Coalescing in the fact table:**

Fact tables replace NULL dimension keys with the unknown member's surrogate key so NULLs never propagate. See [examples/fct_single_source.sql](../examples/fct_single_source.sql) for the full pattern. The coalesce must reuse the same natural-key expression (including default values such as `-1` or the `unknown_member_label`) that the dimension uses to compute the unknown-member hash:

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

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

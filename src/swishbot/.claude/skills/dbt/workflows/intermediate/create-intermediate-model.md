# Create Intermediate Model

Build a new intermediate model to isolate complex logic between staging and marts.

## Step 1: Confirm Intermediate Is Needed

Create an intermediate model when:

- A mart would require **4-5+ joins** without one — break the complexity into steps
- You need to **change the grain** (fan out by quantity, collapse to a different entity)
- A **complex transformation** (pivoting, window functions, business logic) should be isolated for testability
- **Multiple marts** need the same prepared dataset — DRY up the logic here

Do NOT create intermediate models for:

- Simple 1-2 join marts — add the joins directly in the mart
- Transformations that only serve one mart and are simple enough to inline

## Step 2: Choose Folder and Name

Organize by **business concern**, not source system. At this layer, data is becoming business-conformed.

```
models/intermediate/
├── finance/
│   ├── _finance__models.yml
│   ├── int_payments_pivoted_to_orders.sql
│   └── int_orders_summed_to_customers.sql
├── marketing/
│   ├── _marketing__models.yml
│   └── int_web_events_sessionized.sql
└── operations/
    ├── _operations__models.yml
    └── int_work_orders_joined_to_properties.sql
```

**Naming pattern:** `int_<entity>s_<verb>ed.sql`

The verb describes what transformation the model performs:

| Verb | Use When |
|------|----------|
| `joined` | Combining two entities |
| `pivoted` | Restructuring rows to columns |
| `aggregated_to_<entity>` | Rolling up to a coarser grain |
| `fanned_out_by_<entity>` | Exploding to a finer grain |
| `filtered` | Applying business rules to include/exclude rows |
| `unioned` | Combining equivalent datasets from multiple sources |
| `sessionized` | Grouping events into sessions |
| `deduplicated` | Removing duplicate records |

Keep the double underscore **only** when operating at the source-system level (e.g., `int_shopify__orders_summed`). Drop it when the model operates across sources or at a business-concept level.

## Step 3: Set Materialization

Default to **ephemeral**. Intermediate models are a development convenience — they should not materialize as tables or views in production.

```yaml
# dbt_project.yml
models:
  intermediate:
    +materialized: ephemeral
```

If an intermediate model is expensive to compute and referenced by multiple downstream models, consider materializing as a **view** in a restricted schema that end users cannot access.

## Step 4: Write the Model

### Pattern: Joining Staged Models

```sql
with

orders as (
    select * from {{ ref('stg_jaffle_shop__orders') }}
),

payments as (
    select * from {{ ref('stg_stripe__payments') }}
),

orders_with_payments as (
    select
        orders.order_id,
        orders.customer_id,
        orders.order_date,
        payments.payment_method,
        payments.amount
    from orders
    inner join payments
        on orders.order_id = payments.order_id
)

select * from orders_with_payments
```

### Pattern: Aggregating to a Different Grain

```sql
with

order_items as (
    select * from {{ ref('stg_jaffle_shop__order_items') }}
),

aggregated as (
    select
        order_id,
        count(*) as item_count,
        sum(amount) as total_amount
    from order_items
    group by 1
)

select * from aggregated
```

### Pattern: Pivoting

```sql
with

payments as (
    select * from {{ ref('stg_stripe__payments') }}
),

pivoted as (
    select
        order_id,
        sum(case when payment_method = 'credit_card' then amount else 0 end) as credit_card_amount,
        sum(case when payment_method = 'bank_transfer' then amount else 0 end) as bank_transfer_amount
    from payments
    group by 1
)

select * from pivoted
```

## Step 5: Validate

- Intermediate models should **never** be exposed to end users or BI tools
- They should **not** appear in the production schema
- **"Narrow the DAG, widen the tables."** Multiple staging inputs converging into fewer, wider outputs is the expected pattern
- If an intermediate model has multiple downstream dependents, that is a red flag — it may belong as a mart instead

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

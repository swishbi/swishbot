# Create Mart Model

Build a new mart model — the final, business-facing transformation layer.

## Step 1: Confirm Mart Is Needed

Create a mart model when:

- You need a **business entity** that end users will query (customers, orders, invoices)
- A BI tool or semantic layer needs a **stable, wide table** to build metrics on
- You are combining staging and/or intermediate models into a **denormalized, entity-grained** output

Do NOT build separate marts for:

- Different time granularities (`orders_per_day`) — use metrics/semantic layer instead
- Different departments wanting the same entity (`finance_orders`, `marketing_orders`) — build one `orders` mart

## Step 2: Choose Folder and Name

Organize by **department** or business area. Each department gets its own schema in the warehouse.

```
models/marts/
├── finance/
│   ├── _finance__models.yml
│   ├── orders.sql
│   └── payments.sql
├── marketing/
│   ├── _marketing__models.yml
│   └── customers.sql
└── operations/
    ├── _operations__models.yml
    └── work_orders.sql
```

Use **plain entity names** — no prefix, no layer indicator:

- `customers` (not `mart_customers` or `fct_customers`)
- `orders`
- `invoices`
- `work_orders`

Avoid subfolders within a department until you have 10+ marts in that department.

## Step 3: Set Materialization

Build marts as **tables** or **incremental** models. Never views — marts are the performance-optimized layer.

Progression path:
1. Start with `table`
2. Move to `incremental` when build times become excessive

```yaml
# dbt_project.yml
models:
  marts:
    +materialized: table
    finance:
      +schema: finance
    marketing:
      +schema: marketing
```

## Step 4: Write the Model

Build **wide and denormalized** — storage is cheap, compute is expensive. Include all relevant data.

- **Entity-grained** — each row represents one discrete instance of a concept (one customer, one order)
- **Include related data** — bring in dimensions from other entities rather than forcing users to join

### Pattern: Simple Mart

```sql
with

orders as (
    select * from {{ ref('stg_jaffle_shop__orders') }}
),

payments as (
    select * from {{ ref('int_payments_pivoted_to_orders') }}
),

final as (
    select
        orders.order_id,
        orders.customer_id,
        orders.order_date,
        orders.status,
        payments.credit_card_amount,
        payments.bank_transfer_amount,
        payments.total_amount
    from orders
    left join payments
        on orders.order_id = payments.order_id
)

select * from final
```

### Pattern: Wide Denormalized Entity

```sql
with

customers as (
    select * from {{ ref('stg_jaffle_shop__customers') }}
),

orders as (
    select * from {{ ref('orders') }}
),

customer_orders as (
    select
        customer_id,
        min(order_date) as first_order_date,
        max(order_date) as most_recent_order_date,
        count(*) as order_count,
        sum(total_amount) as lifetime_value
    from orders
    group by 1
),

final as (
    select
        customers.customer_id,
        customers.first_name,
        customers.last_name,
        customer_orders.first_order_date,
        customer_orders.most_recent_order_date,
        customer_orders.order_count,
        coalesce(customer_orders.lifetime_value, 0) as lifetime_value
    from customers
    left join customer_orders
        on customers.customer_id = customer_orders.customer_id
)

select * from final
```

## Step 5: Manage Complexity

- If a mart requires **4-5+ joins**, add intermediate models to break up the complexity
- Two intermediate models (3 concepts each) + one mart is more readable than 6 joins in one mart
- Cross-mart dependencies are allowed but should be deliberate and documented

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

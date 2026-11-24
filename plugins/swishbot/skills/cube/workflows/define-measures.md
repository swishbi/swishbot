# Define Measures

Measures are the metrics. Define each one once, in the cube, and give consumers nothing to re-aggregate.

## Step 1: Pick the Type

| Need | `type` | Notes |
|------|--------|-------|
| Total of a column | `sum` | The default for amounts |
| Number of rows | `count` | Counts rows of the cube |
| Distinct things | `count_distinct` | Exact; `count_distinct_approx` for very large tables |
| Average, min, max | `avg`, `min`, `max` | Averages of averages are wrong across groups; prefer `sum` / `count` as a ratio |
| A formula over other measures | `number` | Ratios, margins, differences |

```yaml
    measures:
      - name: total_debit_amount
        sql: debit_amount
        type: sum
        title: "Total debits"
        format: currency
```

## Step 2: Sign Amounts Where Direction Matters

Accounting marts often store amounts positive in each account's natural direction. Summing them across account types adds income to expense. Sign in the measure, once:

```yaml
      - name: net_profit
        sql: >
          case when account_type in ('Income', 'Other Income')
               then net_amount else -net_amount end
        type: sum
        title: "Net profit (income minus expense)"
```

State the sign rule in `description`; it's the definition consumers rely on.

## Step 3: Ratios With `number`

Reference other measures in braces. Guard the denominator.

```yaml
      - name: gross_margin_ratio
        sql: "{gross_profit} / nullif({revenue}, 0)"
        type: number
        format: percent
```

Never average a ratio column from the mart; build it from its parts so it is right at every grouping.

## Step 4: Filtered Measures

A measure can carry its own filter:

```yaml
      - name: overdue_invoice_count
        sql: invoice_id
        type: count_distinct
        filters:
          - sql: "{CUBE}.days_overdue > 0"
```

## Step 5: Balances (Semi-Additive)

A closing balance adds up across accounts but **not across time**. Pick one approach and say so in the description.

**Preferred: build the balance from flows.** Keep the period's net change in the mart and let a rolling window accumulate it:

```yaml
      - name: balance
        sql: net_change_amount
        type: sum
        rolling_window:
          trailing: unbounded
        title: "Balance (cumulative)"
```

The query must group by a time dimension (for example month) for the window to apply.

**Alternative: a closing-balance column.** Expose it as a `sum` measure, document that it is valid only per period, and make every view and report group or filter by the period. Cube can't stop a SQL client from summing it over months, so the description and the views carry the rule.

## Step 6: Describe Every Measure

`title` for people, `description` for the definition: sign rules, inclusions and exclusions, the period it is valid for. Agents read descriptions to choose measures.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

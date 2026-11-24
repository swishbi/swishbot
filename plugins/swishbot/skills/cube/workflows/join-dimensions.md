# Join Dimensions

Connect a fact cube to its dimension cubes so consumers can group a measure by any attribute.

## Step 1: Model Each Dimension as Its Own Cube

A dimension mart (`dim_quickbooks_account`, `dim_date`) gets its own cube with a primary key and its attributes as dimensions. It usually has no measures beyond a count.

## Step 2: Declare the Join on the Fact

Joins live on the cube that holds the foreign key, pointing at the dimension:

```yaml
    joins:
      - name: dim_quickbooks_account
        sql: "{CUBE}.account_id = {dim_quickbooks_account}.account_id"
        relationship: many_to_one
```

| `relationship` | Meaning |
|----------------|---------|
| `many_to_one` | Many fact rows per dimension row (the usual fact → dimension join) |
| `one_to_many` | One row here, many there |
| `one_to_one` | Exactly one each side |

Cube treats joins as left joins from the cube that declares them: a fact row with no matching dimension row still counts in every total.

## Step 3: Check Both Primary Keys

Both cubes need a primary key. Without them Cube can't de-duplicate, and a measure can fan out (count or sum the same fact row more than once).

## Step 4: Join a Date Dimension (Optional)

A `time` dimension on the fact already rolls up to week, month, quarter and year. Join a `dim_date` cube only for attributes Cube can't compute: fiscal periods, holidays, working-day flags.

```yaml
      - name: dim_date
        sql: "{CUBE}.month_start = {dim_date}.date_day"
        relationship: many_to_one
```

## Step 5: Expose the Joined Members in a View

A join alone exposes nothing. List the members a view needs with `join_path`:

```yaml
    cubes:
      - join_path: rpt_quickbooks_profit_and_loss
        includes: [net_profit, month_start]
      - join_path: rpt_quickbooks_profit_and_loss.dim_quickbooks_account
        includes: [account_name, account_type, account_number]
```

## Step 6: Prove the Join Didn't Change Totals

Query the measure ungrouped, then grouped by a dimension attribute. The grouped rows must sum to the ungrouped total (`test-the-model.md`). A difference means fan-out or orphan rows.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

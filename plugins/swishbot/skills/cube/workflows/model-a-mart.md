# Model a Mart as a Cube

Turn one dbt mart into one cube: the table, its primary key, its dimensions and its refresh.

## Step 1: Read the Mart

From the dbt model and its YAML, write down:

- **Grain:** one row per what? (one ledger line; one month × account)
- **Key:** the column, or columns, that make a row unique
- **Columns** and their types: dates, timestamps, numbers, text, booleans
- **Schema and table** the consumers' Cube reads (`finance.rpt_quickbooks_profit_and_loss`)

## Step 2: Create the Cube File

One file per cube, named after the mart: `model/cubes/<mart>.yml`.

```yaml
cubes:
  - name: rpt_quickbooks_profit_and_loss
    title: "Profit and loss"
    description: "One row per month and P&L account."
    sql_table: finance.rpt_quickbooks_profit_and_loss
```

Use `sql_table` for a mart. Reach for `sql:` (a query) only when you must reshape, and prefer fixing the mart instead.

## Step 3: Declare the Primary Key

Cube needs a primary key for joins and for counting correctly.

**Single-column key:**

```yaml
    dimensions:
      - name: posting_id
        sql: posting_id
        type: string
        primary_key: true
```

**Composite key** (common for statement marts): build one string key.

```yaml
      - name: line_key
        sql: "cast({CUBE}.month_start as varchar) || '|' || {CUBE}.account_id"
        type: string
        primary_key: true
        public: false
```

`public: false` hides a member from every view and consumer.

## Step 4: Add Dimensions

| Column type | Dimension `type` |
|-------------|------------------|
| text, id | `string` |
| date or timestamp | `time` |
| number used to group or filter | `number` |
| boolean | `boolean` |

- Every dimension gets a `title` a business user understands.
- A date column is a `time` dimension, so consumers can roll it up to week, month, quarter and year. Don't pre-format dates as text.
- Describe anything non-obvious in `description`; Metabase and agents show it.
- IDs are dimensions too, but agents' views leave them out (see `secure-with-views.md`).

## Step 5: Deny Direct Access

Every cube denies everyone; views grant access.

```yaml
    access_policy:
      - group: "*"
        member_level:
          excludes: "*"
        row_level:
          allow_all: true
```

A view is a member security boundary: when a cube is reached through a view, only the view's policy decides who may query, and only the row level of the cube's policy applies.

## Step 6: Set the Refresh Key

Cube caches query results. The refresh key decides when the cache is stale.

- **A warehouse table rebuilt on a schedule:** a time-based key (`every: 1 hour`) is usually enough.
- **A file-backed source swapped on publish (DuckDB):** use a **data-dependent** key, so results change exactly when the published numbers change.

```yaml
    refresh_key:
      sql: >
        select md5(cast(count(*) as varchar) || '|' ||
                   cast(coalesce(sum(net_amount), 0) as varchar))
        from finance.rpt_quickbooks_profit_and_loss
      every: "1 second"
```

The `every` interval is how often Cube re-runs the key query, not how often it reloads data.

## Step 7: Check It Compiles

Start Cube and query one dimension through a view (`test-the-model.md`). A cube that doesn't compile fails every view that uses it.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

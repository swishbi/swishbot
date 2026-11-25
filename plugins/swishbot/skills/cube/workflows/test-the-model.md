# Prove Cube's Numbers Match the Warehouse

A cube is done when it compiles, its boundaries hold, and its measures equal the mart they read.

## Step 1: Start Cube Locally

Run the project's Cube container (or its compose stack) against development or fixture data, with `CUBEJS_DEV_MODE=false` and the SQL API port set (`CUBEJS_PG_SQL_PORT`). A model error shows in the container log at startup and on the first query.

## Step 2: Query Through the SQL API

Cube's SQL API speaks the Postgres protocol, so `psql` works. Log in as each consumer:

```bash
# port: the one published for CUBEJS_PG_SQL_PORT; dbname: cube
psql "host=localhost port=5432 user=metabase dbname=cube" \
  -c "select month_start, measure(net_profit) from finance_profit_and_loss group by 1 order by 1"
```

`MEASURE(name)` asks for a Cube measure by name. Group by dimensions as usual.

## Step 3: Reconcile Totals With the Mart

For the same filter, Cube's total must equal the mart's total, read straight from the warehouse:

| Check | Cube query | Warehouse query |
|-------|-----------|-----------------|
| Grand total | `measure(net_profit)` ungrouped | the same signed sum over the mart |
| Grouping doesn't change totals | `measure(net_profit)` grouped by `account_type`, summed | the ungrouped total |
| Joins don't fan out | grouped by a joined dimension, summed | the ungrouped total |

Automate these as tests in CI, against fixture data, so a model change can't silently move a number.

## Step 4: Test the Boundaries

For every SQL API user:

- **Allowed:** a query on each view granted to its group succeeds.
- **Refused:** a query on any cube, and on any view not granted to its group, fails.
- **Shared views:** the same query returns the same total to every group that shares the view.
- **Restricted views:** the view lists none of the members its consumer mustn't see.
- **Unknown users** and wrong passwords are refused with the same message.

## Step 5: Check the Model Against dbt

Cube members name mart columns, so a dbt rename can break a cube silently until the first query. A cheap CI check reads dbt's `manifest.json` and the cube YAML and fails when:

- a cube's `sql_table` isn't a mart in the manifest;
- a member's `sql:` names a column the mart doesn't have;
- a `time` dimension's column isn't a date or timestamp;
- a view member that consumers rely on disappears or changes name.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

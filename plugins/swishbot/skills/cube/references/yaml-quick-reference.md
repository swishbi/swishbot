# Cube YAML Quick Reference (Cube Core 1.x)

Keys are shown in `snake_case`, as in Cube's documentation. Cube's YAML compiler also accepts `camelCase` (`access_policy` / `accessPolicy`, `join_path` / `joinPath`). Pick one per project and keep it.

Reference: https://docs.cube.dev/reference/data-modeling

## Cube

| Key | Purpose |
|-----|---------|
| `name` | The cube's id; name it after its mart |
| `sql_table` | The table the cube reads (`schema.table`); or `sql:` for a query |
| `title`, `description` | Shown to people and agents |
| `refresh_key` | `every:` and/or `sql:`; when cached results go stale |
| `joins` | Relationships to other cubes |
| `dimensions`, `measures` | Members |
| `pre_aggregations` | Rollups stored in Cube Store |
| `access_policy` | Who may query the cube; deny-all for cubes reached only through views |

## Dimension

| Key | Purpose |
|-----|---------|
| `sql` | Column or expression; `{CUBE}` refers to this cube |
| `type` | `string`, `number`, `time`, `boolean` |
| `primary_key` | `true` on the key; required for joins and correct counts |
| `public` | `false` hides it from every view and consumer |
| `title`, `description`, `format` | Display |

## Measure

| Key | Purpose |
|-----|---------|
| `sql` | Column or expression; `{other_measure}` in a `number` measure |
| `type` | `sum`, `count`, `count_distinct`, `count_distinct_approx`, `avg`, `min`, `max`, `number` |
| `filters` | `- sql: "{CUBE}.status = 'open'"` |
| `rolling_window` | `trailing: unbounded` for running totals and balances built from flows |
| `format` | `currency`, `percent` |

## Join

```yaml
joins:
  - name: dim_quickbooks_account
    sql: "{CUBE}.account_id = {dim_quickbooks_account}.account_id"
    relationship: many_to_one   # one_to_many, one_to_one
```

## View

```yaml
views:
  - name: finance_profit_and_loss
    access_policy:
      - group: metabase
        row_level:
          allow_all: true
    cubes:
      - join_path: rpt_quickbooks_profit_and_loss
        includes: [net_profit, month_start]          # or "*"; excludes: [...]
      - join_path: rpt_quickbooks_profit_and_loss.dim_quickbooks_account
        prefix: false
        includes:
          - name: account_name
            alias: account
```

In Cube 1.x, view-level `measures:`, `dimensions:` and `joins:` keys are gone; members come in through `cubes:`.

## Access Policy

| Key | Purpose |
|-----|---------|
| `group` / `groups` | Which groups the policy applies to; `"*"` for everyone |
| `member_level` | `includes` / `excludes` member lists; `excludes: "*"` grants nothing |
| `row_level` | `allow_all: true`, or `filters:` in the REST filter format |

Groups come from `contextToGroups` in `cube.js` for Cube Core. Reference: https://docs.cube.dev/reference/data-modeling/data-access-policies

## Pre-Aggregation

```yaml
pre_aggregations:
  - name: monthly_by_account
    measures: [net_profit]
    dimensions: [account_type]
    time_dimension: month_start
    granularity: month
    refresh_key:
      every: 1 hour
```

Pre-aggregations need Cube Store in production. Add them when a query is slow, not before.

## Environment (`cubejs/cube` image)

| Variable | Purpose |
|----------|---------|
| `CUBEJS_DB_TYPE` and the driver's variables | The data source (for example `duckdb` with `CUBEJS_DB_DUCKDB_DATABASE_PATH`) |
| `CUBEJS_PG_SQL_PORT` | Turns on the SQL API (Postgres protocol) |
| `CUBEJS_API_SECRET` | Signs REST API tokens |
| `CUBEJS_DEV_MODE` | `false` in every shared environment |

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

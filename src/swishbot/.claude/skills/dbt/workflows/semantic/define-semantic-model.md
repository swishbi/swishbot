# Define MetricFlow Semantic Model and Metrics

This workflow covers the end-to-end MetricFlow flow for dbt Core users: installing MetricFlow, writing semantic model YAML, defining metrics, validating, and querying.

---

## Step 1 — Install MetricFlow

Install the `dbt-metricflow` package with the extra that matches your dbt adapter:

```bash
pip install "dbt-metricflow[dbt-snowflake]"   # Snowflake
pip install "dbt-metricflow[dbt-bigquery]"    # BigQuery
pip install "dbt-metricflow[dbt-databricks]"  # Databricks
pip install "dbt-metricflow[dbt-postgres]"    # Postgres
pip install "dbt-metricflow[dbt-duckdb]"      # DuckDB
```

Verify the install:

```bash
mf --version
```

> **Note:** `mf` is the CLI for dbt Core. `dbt sl` commands require a dbt Cloud connection and will not work with dbt Core alone.

---

## Step 2 — Choose a Mart and Identify Semantic Objects

Semantic models sit one layer above marts — only build on stable, fully-tested mart models. Never write a semantic model against a staging or intermediate model.

For the chosen mart, identify:

| Object | What It Is | Example |
|--------|-----------|---------|
| **Primary entity** | The grain of the mart — the unique identifier for each row | `order_id` on `fct_orders` |
| **Foreign entities** | FK columns that join to other semantic models or dimensions | `customer_id`, `product_id` |
| **Time dimensions** | Date/timestamp columns for time-series grouping | `order_date` |
| **Categorical dimensions** | String columns for filtering and grouping | `status`, `region`, `channel` |
| **Measures** | Numeric columns you will aggregate | `revenue`, `quantity`, `discount_amount` |

Supported aggregation types: `sum`, `count`, `avg`, `min`, `max`, `count_distinct`.

---

## Step 3 — Write the Semantic Model YAML

Co-locate the semantic model YAML with the mart's existing schema YAML file, or create a dedicated `<mart_name>__semantic_model.yml` in the same folder.

```yaml
semantic_models:
  - name: orders                         # Unique name for this semantic model
    model: ref('fct_orders')             # Must reference a mart via ref()
    description: "Order-level fact table — one row per order."

    entities:
      - name: order                      # Primary entity — matches the grain
        type: primary
        expr: order_id                   # Column that uniquely identifies each row

      - name: customer                   # Foreign entity — joins to a customer semantic model
        type: foreign
        expr: customer_id

    dimensions:
      - name: order_date                 # Time dimension — required for metric_time grouping
        type: time
        type_params:
          time_granularity: day          # Mandatory: day | week | month | quarter | year
        expr: order_date

      - name: status                     # Categorical dimension
        type: categorical
        expr: status

    measures:
      - name: revenue                    # Measure name referenced by metrics
        agg: sum                         # Aggregation: sum | count | avg | min | max | count_distinct
        expr: revenue                    # Column or expression to aggregate
        description: "Gross revenue before discounts."
        create_metric: true             # Shortcut: auto-generates a simple metric named 'revenue'

      - name: order_count
        agg: count_distinct
        expr: order_id
        description: "Count of distinct orders."
        create_metric: true

      - name: discount_amount
        agg: sum
        expr: discount_amount
        description: "Total discount applied."
```

**Key points:**
- `type_params.time_granularity` on a time dimension is **mandatory** — MetricFlow uses it to power `metric_time` grouping and time-grain queries.
- `create_metric: true` on a measure generates a simple metric automatically. Use this for straightforward sum/count metrics; write explicit metric YAML for ratios, derived, or cumulative types.
- The `expr` field can be a column name or any SQL expression valid in the warehouse dialect.

---

## Step 4 — Define Metric YAML

Place metrics in `_metrics.yml` alongside the semantic model file. Four metric types are available in dbt Core:

### Simple metric

```yaml
metrics:
  - name: revenue
    label: "Total Revenue"
    description: "Sum of gross revenue."
    type: simple
    type_params:
      measure: revenue                   # References a measure name in the semantic model
```

### Ratio metric

```yaml
  - name: average_order_value
    label: "Average Order Value"
    description: "Revenue divided by order count."
    type: ratio
    type_params:
      numerator: revenue                 # Measure name
      denominator: order_count          # Measure name
```

### Derived metric

```yaml
  - name: net_revenue
    label: "Net Revenue"
    description: "Revenue minus discounts."
    type: derived
    type_params:
      expr: "{{ Metric('revenue') }} - {{ Metric('discount_amount') }}"
      metrics:
        - name: revenue
        - name: discount_amount
```

### Cumulative metric

```yaml
  - name: revenue_7d
    label: "Revenue (Last 7 Days)"
    description: "Rolling 7-day sum of revenue."
    type: cumulative
    type_params:
      input_metric: revenue
      window: 7 days
```

---

## Step 5 — Validate

Run offline validation first (fast — checks YAML structure and MetricFlow logic without hitting the warehouse):

```bash
mf validate-configs --skip-dw
```

Then run full validation including a warehouse round-trip:

```bash
mf validate-configs
```

Fix any errors before querying. Common issues:
- Missing `type_params.time_granularity` on a time dimension
- Measure name in a metric does not match the semantic model measure name
- `model: ref(...)` references a model that does not exist or is not a mart

---

## Step 6 — Query and Iterate

```bash
# List all available metrics
mf list metrics

# List valid group-by dimensions for a specific metric
mf list dimensions --metrics revenue

# Basic time-series query
mf query --metrics revenue --group-by metric_time

# Query with a specific time granularity
mf query --metrics revenue --group-by metric_time__month

# Multi-metric query with a row limit
mf query --metrics revenue,order_count --group-by metric_time --limit 10

# Inspect the generated SQL without executing
mf query --metrics revenue --group-by metric_time --explain

# Filter with a dimension value (note the Dimension() template syntax)
mf query --metrics revenue \
  --where "{{ Dimension('order__status') }} = 'completed'"
```

> **Tip:** The dbt MCP server may also support querying semantic models interactively — check `mf list metrics` output and the MCP server's tool list to see what's available in your session.

---

## dbt Core Limitations

| Capability | dbt Core |
|-----------|----------|
| Define semantic models + metrics in YAML | ✓ |
| `mf` CLI to validate and query locally | ✓ |
| dbt MCP server for interactive metric queries | ✓ |
| BI tool connectivity via Semantic Layer API | ✗ (dbt Cloud only) |
| `dbt sl` commands | ✗ (require dbt Cloud connection) |

---

## Checklist

- [ ] MetricFlow installed using the correct dbt adapter package (e.g., `dbt-metricflow[dbt-snowflake]`)
- [ ] Semantic model references a stable, tested mart via `model: ref('...')`
- [ ] Primary entity matches the mart's grain column
- [ ] All time dimensions have `type_params.time_granularity` set
- [ ] All measures have `agg` and either an `expr` or the column name matches the measure name
- [ ] `mf validate-configs --skip-dw` passes
- [ ] `mf validate-configs` passes against the warehouse
- [ ] At least one metric queries successfully with `mf query`

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

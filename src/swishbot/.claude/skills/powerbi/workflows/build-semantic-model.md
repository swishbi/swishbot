# Build Semantic Model

## Purpose

Create or edit the Power BI semantic model: configure parameterized M queries, import tables, define relationships, write DAX measures, build reusable framework tables, and apply naming conventions. This workflow assumes you have a model blueprint from the [Design Semantic Model](design-semantic-model.md) workflow.

See [examples/semantic_model.tmdl](../examples/semantic_model.tmdl) for a complete reference model in TMDL format.

## Prerequisites

- Model blueprint (tables, relationships, RLS plan) from design workflow
- A dedicated `.pbix` file for the semantic model (not a report file)
- Access to the warehouse with a service account or AAD credentials
- Power BI Desktop installed

## Steps

### 1. Create Power Query Parameters

Before writing any M queries, create parameters for every connection variable. The exact set depends on the warehouse platform.

**Snowflake example:**

| Parameter | Type | Example (DEV) |
|-----------|------|---------------|
| `HostName` | Text | `account.snowflakecomputing.com` |
| `WarehouseName` | Text | `DEVELOPER_WH` |
| `RoleName` | Text | `DEVELOPER` |
| `DbName` | Text | `ANALYTICS_DEV` |
| `SchemaName` | Text | `DBT_EPHILLIPS` |

**SQL Server / Azure SQL example:**

| Parameter | Type | Example (DEV) |
|-----------|------|---------------|
| `DbServer` | Text | `myserver.database.windows.net` |
| `DbName` | Text | `analytics_dev` |
| `DbSchema` | Text | `marts` |

**Databricks example:**

| Parameter | Type | Example (DEV) |
|-----------|------|---------------|
| `HostName` | Text | `adb-1234567890.1.azuredatabricks.net` |
| `HttpPath` | Text | `/sql/1.0/warehouses/abc123` |
| `CatalogName` | Text | `analytics_dev` |
| `SchemaName` | Text | `marts` |

**BigQuery example:**

| Parameter | Type | Example (DEV) |
|-----------|------|---------------|
| `ProjectId` | Text | `my-project-dev` |
| `DatasetName` | Text | `marts` |

These parameters are swapped automatically by deployment pipelines when promoting from DEV → TEST → PROD. Never hardcode server, database, or schema names in M queries.

### 2. Write Parameterized M Queries

For each table in the blueprint, write an M query that uses the parameters. Organize queries into query groups: `Facts` for fact tables, `Dimensions` for dimension tables, `Parameters` for the parameters themselves.

**Snowflake pattern (with auto-renaming):**

```m
let
    Source = Snowflake.Databases(HostName, WarehouseName, [Role=RoleName]),
    Result = Table.TransformColumnNames(
        Source{[Name=DbName]}[Data]{[Name=SchemaName]}[Data]{[Name="FCT_ORDERS"]}[Data],
        each Text.Proper(Text.Trim(Text.Replace(_, "_", " ")))
    )
in
    Result
```

The `Table.TransformColumnNames` step converts `SNAKE_CASE` column names from Snowflake into `Title Case` for Power BI (e.g., `ORDER_DATE` → `Order Date`). This is the only acceptable transformation in M — it doesn't alter data, only display names.

**SQL Server / Azure SQL pattern:**

```m
let
    Source = Sql.Database(DbServer, DbName),
    Schema = Source{[Schema = DbSchema]}[Data],
    Table = Schema{[Name = "dim_customers"]}[Data]
in
    Table
```

**Databricks pattern:**

```m
let
    Source = Databricks.Catalogs(HostName, HttpPath, [Catalog=CatalogName]),
    Schema = Source{[Name=SchemaName]}[Data],
    Table = Schema{[Name = "dim_customers"]}[Data]
in
    Table
```

| Parameter | Type | Example (DEV) |
|-----------|------|---------------|
| `HostName` | Text | `adb-1234567890.1.azuredatabricks.net` |
| `HttpPath` | Text | `/sql/1.0/warehouses/abc123` |
| `CatalogName` | Text | `analytics_dev` |
| `SchemaName` | Text | `marts` |

**BigQuery pattern:**

```m
let
    Source = GoogleBigQuery.Database([BillingProject=ProjectId]),
    Dataset = Source{[Name=DatasetName]}[Data],
    Table = Dataset{[Name = "dim_customers"]}[Data]
in
    Table
```

| Parameter | Type | Example (DEV) |
|-----------|------|---------------|
| `ProjectId` | Text | `my-project-dev` |
| `DatasetName` | Text | `marts` |

**PostgreSQL pattern:**

```m
let
    Source = PostgreSQL.Database(DbServer, DbName),
    Schema = Source{[Schema = DbSchema]}[Data],
    Table = Schema{[Name = "dim_customers"]}[Data]
in
    Table
```

The PostgreSQL pattern uses the same parameters as SQL Server / Azure SQL. The only difference is the connector function (`PostgreSQL.Database` vs `Sql.Database`).

Key rules:

- **No data transformations in M** — the warehouse owns all transformation logic. M queries should only select the table. Column renaming via `Table.TransformColumnNames` is the sole exception.
- **No column removal in M** — if a column shouldn't be in the model, remove it from the dbt mart, not in Power Query.
- **Folding must be preserved** — avoid M steps that break query folding (e.g., `Table.Buffer`, custom functions on columns). If folding breaks, the entire table is pulled into memory before filtering.

### 3. Configure Model Properties

Set these properties on the model before adding any content:

- **`discourageImplicitMeasures`** — prevents users from accidentally dragging numeric columns into visuals as implicit SUM/COUNT aggregations. All aggregation must go through explicit DAX measures.
- **`culture: en-US`** — sets the default locale for formatting.

### 4. Configure Relationships

Create relationships following the blueprint:

- **Type**: Many-to-one (fact → dimension) in all cases
- **Cross-filter direction**: Single (dimension filters fact, not the reverse). Only use bi-directional when explicitly required and documented (e.g., bridge tables for many-to-many relationships).
- **Active relationships**: One active relationship per column pair. For role-playing dimensions (e.g., `DimDate` used as lead date, approved date, and closed date on a fact), create one active and multiple inactive relationships. Use `USERELATIONSHIP` in DAX measures for the inactive ones.
- **Foreign key columns**: Hide all key/FK columns in a `_hidden` display folder — end users should never see or use them directly.

### 5. Build Reusable Framework Tables

Every semantic model includes a set of underscore-prefixed framework tables that are consistent across all client engagements. These are calculated tables or calculation groups — they contain no client data.

#### `_Measures` — Centralized Measure Table

All business measures live in a single `_Measures` table rather than scattered across fact tables. This provides a single location for all measures and clean display folder organization.

Display folder conventions:

- `_Base Measures` — foundational measures referenced by others
- `Financials\A/R`, `Financials\Profitability`, `Sales\Leads`, etc. — business-domain grouping
- `Time Intelligence\Period-over-period growth` — time comparison measures
- `Time Intelligence\Period-to-date growth` — YTD/QTD/WTD comparisons
- `Time Intelligence\Period-to-date total` — cumulative period totals
- `Time Intelligence\Moving annual total growth` — MAT/LTM measures
- `Time Intelligence\Moving averages` — rolling averages (4W, 1Q, 1Y)

#### `_CalcTimeIntelligence` — Calculation Group

A calculation group that applies time intelligence transformations to any measure via `SELECTEDMEASURE()`. Standard calculation items:

| Item | Purpose |
|------|---------|
| `CY` | Current period (passthrough) |
| `PY` | Prior year equivalent |
| `YoY` | Year-over-year variance |
| `YoY %` | Year-over-year variance as percentage |
| `YTD` | Year-to-date cumulative |
| `PYTD` | Prior year-to-date |
| `YoYTD` | Year-over-year year-to-date variance |
| `YoYTD %` | Year-over-year year-to-date as percentage |
| `PP` | Prior period (dynamic — adapts to Day/Week/Month/Quarter/Year based on `ISINSCOPE`) |
| `PoP` | Period-over-period variance (dynamic) |
| `PoP %` | Period-over-period variance as percentage (dynamic) |

**When to use the calculation group vs. explicit measures:**

- **Calculation group** — best for slicer-driven scenarios where the user selects the time comparison type from a dropdown. One slicer controls the time intelligence applied to all visuals on the page.
- **Explicit measures** (e.g., `KPI YoY`, `KPI QoQ`) — best for visuals that show multiple time comparisons side-by-side in a single table or card layout (e.g., a row showing CY, PY, YoY, and YoY% simultaneously). Calculation groups apply to the entire visual, so you cannot show CY and PY as separate columns using only the calc group.

Both approaches should exist in the model. They use the same underlying DAX logic.

#### KPI Switcher Pattern

The `KPI` measure is the central dispatch:

```dax
KPI =
SWITCH(
    SELECTEDVALUE( _PrmKPI[_PrmKPI Fields] ),
    "'_Measures'[Total Sales]", [Total Sales],
    "'_Measures'[Contract Amount]", [Contract Amount],
    // ... all selectable measures
    BLANK()
)
```

All time intelligence measures reference `[KPI]` instead of a specific business measure. When the user selects a different KPI from the `_PrmKPI` slicer, the entire time intelligence chain updates automatically. Write once, apply to all.

#### Highlight Measures

Conditional formatting measures that return hex color codes based on variance direction:

```dax
KPI PoP Highlight =
VAR _red = "#D64550"
VAR _green = "#1AAB40"
VAR _value = [KPI PoP]
VAR VarianceGreaterthan0 = IF ( _value >= 0, _green )
VAR VarianceLessthan0 = IF ( _value < 0, _red )
RETURN
    COALESCE ( VarianceGreaterthan0, VarianceLessthan0, "#000000" )
```

Consider consolidating these into a calculation group to avoid repeating the same red/green logic for each time comparison variant.

#### `ShowValueForDates` Guard

A measure on the `DimDate` table that prevents showing data for future periods:

```dax
ShowValueForDates =
VAR LastDateWithData = CALCULATE( MAX( FctTable[Date] ), REMOVEFILTERS() )
VAR FirstDateVisible = MIN( DimDate[Date Day] )
RETURN FirstDateVisible <= LastDateWithData
```

Every time intelligence measure wraps its logic in `IF([ShowValueForDates], ...)` so blank/future periods don't show misleading zeros.

#### Field Parameters

Field parameters let users dynamically switch what a visual displays without editing the report:

| Table | Purpose | Example Entries |
|-------|---------|-----------------|
| `_PrmKPI` | Switch the active business metric | Total Sales, Contract Amount, Lead Count (with category grouping) |
| `_PrmDimension` | Switch the grouping dimension | Location, Company Rep, Job Category, Trade Type |
| `_PrmDateHierarchy` | Switch the date granularity | Year, Quarter, Month, Week, Day (with a Divisor column for period-count calculations) |
| `_PrmPeriodHierarchy` | Switch the period level for comparisons | Year, Quarter, Month |
| `_PrmReferenceDate` | Switch which role-playing date column is active | Lead Date, Approved Date, Closed Date |

Each field parameter follows the same TMDL structure: a display column, a hidden `Fields` column (with `ParameterMetadata`), and a hidden `Order` column for sorting.

#### Model Metadata Tables

Self-documenting tables that expose the model's own structure:

| Table | Source | Purpose |
|-------|--------|---------|
| `_MdlTables` | `INFO.VIEW.TABLES()` | Lists all tables in the model |
| `_MdlColumns` | `INFO.VIEW.COLUMNS()` | Lists all columns with data types, visibility, sort-by |
| `_MdlMeasures` | `INFO.VIEW.MEASURES()` | Lists all measures with expressions |
| `_MdlRelationships` | `INFO.VIEW.RELATIONSHIPS()` | Lists all relationships with cardinality and filter direction |

These are development/debugging aids — they can be hidden from end users.

#### `_DatasetRefreshDate`

A table with a single M partition that queries the warehouse for the current timestamp:

```m
let
    Source = Snowflake.Databases(HostName, WarehouseName, [Role=RoleName]),
    Database = Source{[Name=DbName,Kind="Database"]}[Data],
    CustomQuery = Value.NativeQuery(Database, "select current_timestamp() as now", null, [EnableFolding=true])
in
    CustomQuery
```

Paired with a measure: `Dataset Last Refreshed = "Dataset Last Refreshed: " & MAX( _DatasetRefreshDate[now] )`. This gives report consumers a visible indicator of data freshness.

### 6. Write Business Measures

With the framework tables in place, write the client-specific business measures in `_Measures`:

**General rules:**

- Names must be specific and unambiguous — avoid `Amount`, `Count`, `Total` on their own
- Include the unit or qualifier: `Total Revenue (Excl Tax)`, `Active Customer Count (30d)`
- Use display folders to group related measures by business domain
- Add `///` documentation comments on every measure explaining what it calculates and including examples for non-obvious logic
- Measures that reference role-playing date relationships use `USERELATIONSHIP`

**After writing business measures:**

- Add each measure to the `_PrmKPI` field parameter (with category and sort order)
- The `KPI` switcher measure, all time intelligence measures, and the calculation group automatically apply to the new measure — no additional DAX needed

### 7. Apply TMDL Format (If Version-Controlled)

When the semantic model is managed in source control (e.g., via Tabular Editor or the TMDL format), follow the TMDL file structure for measures, tables, and relationships. This enables proper diff/merge workflows. See [examples/semantic_model.tmdl](../examples/semantic_model.tmdl) for the full structure.

### 8. Configure Refresh

- **Import mode** (default): Set up scheduled refresh in the Power BI service after publishing
- **DirectQuery**: Only for tables that need real-time data and where the warehouse can handle the query load
- **Composite models**: Mix import and DirectQuery only when latency requirements differ across tables

### 9. Validate

Before publishing:

- Verify all relationships are correct (check the model diagram view)
- Test DAX measures against known values from the warehouse
- Confirm query folding is active on all import tables (check the M query plan)
- Verify parameters are used everywhere — search for hardcoded server/database strings
- Confirm `discourageImplicitMeasures` is enabled
- Check that all key/FK columns are hidden in `_hidden` display folders

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

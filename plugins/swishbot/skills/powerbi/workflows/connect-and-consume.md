# Connect and Consume

## Purpose

Connect to the published semantic model from Excel and other external tools instead of exporting data. This preserves governance, keeps a single source of truth, and lets users work in their preferred tools.

## Prerequisites

- Semantic model is published to the Power BI service
- Users have at least Build permission on the semantic model (or Viewer access with "Allow users to connect to the dataset" enabled)
- For Excel: Excel 2016+ on Windows, or Microsoft 365 on Mac (with limitations)

## Steps

### 1. Connect from Excel (Pivot Tables)

This is the primary consumption pattern for users who need to "export" data for ad-hoc analysis.

**On Windows:**

1. Open Excel
2. **Data → Get Data → From Power BI** (or **Insert → PivotTable → From Power BI**)
3. Select the published semantic model
4. Build pivot tables, pivot charts, and formulas against the live connection
5. Save the workbook — it contains only the connection and layout, not the data itself

**On Mac (Microsoft 365):**

1. Open Excel
2. **Insert → PivotTable → From Power BI**
3. Select the semantic model
4. Note: Mac support is more limited — some features (like cube formulas) may not be available

**Key benefits over exporting:**

- Data is always current (refreshes when the workbook is opened or manually refreshed)
- RLS is enforced — each user sees only their permitted data
- No stale CSV files floating around in email or shared drives
- The semantic model's measures and hierarchies are available in the pivot field list

### 2. Use Cube Formulas (Advanced Excel)

For users who need specific cell-level values rather than pivot tables:

```excel
=CUBEVALUE("PowerBIModel", "[Measures].[Total Revenue (Gross)]", "[dim_date].[fiscal_year].&[2025]")
```

Cube formulas let users build custom layouts while still connected to the semantic model. They are particularly useful for:

- Formatted management reports that don't fit a pivot table layout
- Dashboards in Excel that combine data from the model with local calculations
- Templates that are shared across the organization

### 3. Connect from Other Tools

**Analyze in Excel (from Power BI service):**

1. In the Power BI service, navigate to the semantic model
2. Click **Analyze in Excel** — this downloads an `.odc` connection file
3. Open the `.odc` file in Excel — it auto-connects to the model

**XMLA endpoint (for third-party tools):**

Premium/PPU workspaces expose an XMLA endpoint that any Analysis Services-compatible tool can connect to:

- Tabular Editor (model development and ALM)
- DAX Studio (query debugging and optimization)
- SQL Server Management Studio
- Python (`pyadomd` or `adomd.net` via `pythonnet`)

Connection string format:

```
Data Source=powerbi://api.powerbi.com/v1.0/myorg/<workspace-name>;Initial Catalog=<dataset-name>
```

### 4. Handle Common Objections

| Objection | Response |
|-----------|----------|
| "I need the raw data in Excel" | You can build a pivot table that shows row-level detail — expand the hierarchy or add all fields. If you truly need raw data, query the warehouse directly; don't export from Power BI. |
| "I need to combine Power BI data with my own spreadsheet" | Use cube formulas to pull specific values into cells, then reference those cells in your formulas. The connection stays live. |
| "It's too slow" | Check that the semantic model is in Import mode (not DirectQuery). If it is Import and still slow, optimize the model — reduce cardinality, remove unused columns. |
| "I'm on Mac and features are missing" | Acknowledged limitation. Use the Power BI service directly for consumption, or use a Windows VM for full Excel integration. |

### 5. Governance Considerations

- **Track usage**: Use the Power BI activity log to monitor who connects via XMLA or Analyze in Excel
- **Build permissions**: Only grant Build permission to users who need to create their own reports or Excel connections. Viewers can consume apps but not connect externally unless explicitly allowed.
- **Disable export if possible**: In tenant settings, consider disabling "Export data" to nudge users toward live connections. This is a tenant-wide setting — coordinate with the Power BI admin.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

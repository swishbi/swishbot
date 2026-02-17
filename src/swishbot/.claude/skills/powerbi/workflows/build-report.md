# Build Report

## Purpose

Build a Power BI report against a published semantic model using a live connection. Reports are separate `.pbix` files that do not contain data — they connect to the shared semantic model.

## Prerequisites

- Semantic model is published to the Power BI service
- You have a separate `.pbix` file for the report (not the model file)
- Business requirements specify which metrics and dimensions to visualize
- Target audience groups are identified

## Steps

### 1. Connect to the Semantic Model

In Power BI Desktop:

1. **Get Data → Power BI datasets** (or "Power BI semantic models")
2. Select the published semantic model
3. The report now has a live connection — no data is stored in the report file

Never use Import or DirectQuery from the report file. The semantic model owns the data connection.

### 2. Plan the Report Layout

Before adding visuals:

- **One page per topic** — each page answers a specific set of questions (e.g., "Sales Overview", "Customer Retention", "Product Performance")
- **3–5 visuals per page** — more than that creates cognitive overload. If you need more, add a drill-through page
- **Top-left anchor** — place the most important KPI card or visual in the top-left corner (users scan left-to-right, top-to-bottom)
- **Consistent filter bar** — use a common slicer panel or filter pane position across all pages

### 3. Build Visuals

General rules:

- **Use the right chart type**: Bar/column for comparison, line for trends over time, card for single KPIs, table/matrix for detail. Avoid pie charts for more than 3–4 categories.
- **Reference measures from the semantic model** — do not create report-level measures unless absolutely necessary (e.g., a one-off calculation for this specific report). If a measure is useful to others, add it to the semantic model.
- **Format consistently** — same number format, same color palette, same font across all visuals. Use the theme file for centralized control.
- **Label clearly** — every visual needs a title that tells the user what they're looking at. Axis labels should use the display name from the semantic model.

### 4. Configure Filters and Slicers

- **Page-level slicers** — for dimensions that filter all visuals on the page (e.g., date range, region)
- **Visual-level filters** — for narrowing a single visual without affecting others
- **Sync slicers** — sync common slicers (like date) across pages so the user's selection persists
- **Default filter values** — set sensible defaults (e.g., current month, user's region) to avoid blank-state confusion

### 5. Add Drill-Through Pages

For detail views:

- Create a drill-through page filtered by a specific dimension (e.g., drill from summary → customer detail)
- Keep drill-through pages focused — they answer "tell me more about this one thing"
- Add a back button so users can return to the summary

### 6. Configure Bookmarks (If Using Audiences)

If different audiences see different views of the same page:

- Create bookmarks that show/hide visuals relevant to each audience
- Use bookmark navigator buttons for user-driven toggling
- Combine with app audience configuration for role-based default views

### 7. Apply a Theme

- Use a JSON theme file for colors, fonts, and formatting consistency
- Store the theme in source control alongside the report `.pbix`
- Apply the theme via **View → Themes → Browse for themes**

### 8. Validate

Before publishing:

- Verify all visuals load correctly and show expected data
- Test slicers and filters — do they interact correctly?
- Check performance — use the Performance Analyzer to identify slow visuals
- Verify the report works on Power BI mobile (if applicable)
- Have the target audience review a draft in the DEV workspace

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

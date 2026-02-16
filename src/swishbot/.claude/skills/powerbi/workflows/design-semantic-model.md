# Design Semantic Model

## Purpose

Plan the semantic model before building it: decide which tables to import from the warehouse, validate star schema readiness, and determine whether to use a single model or split into multiple models.

## Prerequisites

- Mart layer tables (`dim_*`, `fct_*`) exist in the warehouse
- Business requirements are documented (which metrics and dimensions are needed)
- You know the target Power BI capacity type (PPU, Premium, Pro)

## Steps

### 1. Inventory Warehouse Tables

List all `dim_*` and `fct_*` tables from the mart layer that are relevant to the business requirements. For each table, note:

- Row count and approximate size
- Grain (what one row represents)
- Refresh frequency needed
- Whether it contains sensitive data requiring RLS

### 2. Validate Star Schema Readiness

Confirm the warehouse tables form a clean star schema:

- Every fact table has surrogate foreign keys pointing to dimension tables
- No fact-to-fact joins are needed (if they are, an intermediate model is missing)
- Dimensions are denormalized — no snowflake chains (if `dim_products` → `dim_categories` exists, flatten it in dbt first)
- Unknown member rows exist in dimensions so NULL foreign keys are never needed

If any of these fail, fix it in the dbt layer before proceeding. The semantic model should not reshape data.

### 3. Assess Model Boundaries

Default to a **single semantic model**. Only split if:

- **RLS cannot express the boundary** — e.g., completely separate business units with no shared dimensions and fundamentally different security models
- **Dataset size exceeds capacity** — the total model size in memory would exceed your Premium/PPU capacity limits
- **Refresh windows conflict irreconcilably** — one fact table needs 15-minute refresh while others are daily, and DirectQuery is not viable

Document the decision and rationale. Every split introduces conformance risk — two models can define the same measure differently.

### 4. Plan Relationships

Map the relationships that will be created in the semantic model:

- Fact → Dimension relationships (many-to-one, single direction by default)
- Cross-filter direction (single unless bi-directional is explicitly required — bi-directional filters cause performance issues and ambiguous results)
- Role-playing dimensions (e.g., `dim_date` used as both order date and ship date on a fact — requires inactive relationships and `USERELATIONSHIP`)

### 5. Plan Row-Level Security (If Needed)

If the model requires RLS:

- Define security roles and the DAX filter expressions
- Map roles to Azure AD groups
- Determine whether dynamic RLS (table-driven) or static RLS (hardcoded) is appropriate
- Prefer dynamic RLS with a security mapping table in the warehouse

### 6. Document the Model Blueprint

Produce a summary:

- Tables to import (with grain and estimated row counts)
- Relationship map
- Single vs. split decision with rationale
- RLS roles (if any)
- Refresh strategy (import scheduled refresh vs. DirectQuery)

This blueprint feeds directly into the [Build Semantic Model](build-semantic-model.md) workflow.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

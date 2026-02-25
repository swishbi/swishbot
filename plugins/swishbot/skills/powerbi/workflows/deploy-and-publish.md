# Deploy and Publish

## Purpose

Set up Power BI workspaces, deployment pipelines, apps, and refresh schedules to move content from development to production safely.

## Prerequisites

- Power BI Premium Per User (PPU) or Premium capacity (deployment pipelines require Premium)
- Semantic model and reports are built and validated in Power BI Desktop
- Azure AD groups exist for audience segmentation (or will be created)

## Steps

### 1. Create Workspaces

Create three workspaces following this naming convention:

| Environment | Workspace Name | Purpose |
|-------------|---------------|---------|
| DEV | `<Project> [DEV]` | Active development and authoring |
| TEST | `<Project> [TEST]` | UAT and stakeholder review |
| PROD | `<Project> [PROD]` | End-user consumption |

Workspace settings:

- Assign each workspace to Premium capacity (or PPU)
- Set workspace access: developers get Admin/Member on DEV, Viewer on TEST/PROD
- Enable the workspace as a pipeline stage (done automatically when creating the pipeline)

### 2. Create a Deployment Pipeline

In the Power BI service:

1. **Deployment pipelines → Create a pipeline**
2. Name it after the project (e.g., `Sales Analytics Pipeline`)
3. Assign the three workspaces to the DEV, TEST, and PROD stages

### 3. Configure Pipeline Rules

Set deployment rules so parameters are swapped automatically during promotion:

| Parameter | DEV | TEST | PROD |
|-----------|-----|------|------|
| `DbServer` | `dev-server.database.windows.net` | `test-server.database.windows.net` | `prod-server.database.windows.net` |
| `DbName` | `analytics_dev` | `analytics_test` | `analytics_prod` |
| `DbSchema` | `marts` | `marts` | `marts` |

This is why M queries must be parameterized (see [Build Semantic Model](build-semantic-model.md)) — the pipeline swaps these values during promotion, so the same model points to different environments without any manual query editing.

### 4. Publish to DEV

From Power BI Desktop:

1. **Publish → Select the DEV workspace**
2. Publish the semantic model `.pbix` first
3. Publish each report `.pbix` (they will auto-connect to the semantic model in the DEV workspace)

### 5. Configure Scheduled Refresh

In the DEV workspace (after publishing):

1. Go to the semantic model settings
2. **Gateway connection** — configure if the data source requires an on-premises gateway
3. **Data source credentials** — authenticate with the warehouse
4. **Scheduled refresh** — set the refresh frequency (e.g., daily at 6:00 AM)
5. **Refresh failure notifications** — configure email alerts for failures

Note: Refresh schedules are workspace-specific. After promoting to TEST/PROD, configure refresh schedules in those workspaces too.

### 6. Promote Through the Pipeline

Promotion workflow:

1. **DEV → TEST**: Deploy when features are ready for UAT. Stakeholders review in the TEST workspace.
2. **TEST → PROD**: Deploy after stakeholder sign-off. End users see changes in PROD.

During promotion:

- The pipeline copies content to the target workspace
- Parameter rules swap database connections automatically
- Refresh schedules in the target workspace are preserved (not overwritten)
- RLS roles and mappings are promoted with the model

Never publish directly to TEST or PROD from Power BI Desktop. Always promote through the pipeline.

### 7. Create a Power BI App

In the PROD workspace:

1. **Create app**
2. Set the app name and description
3. **Configure up to 10 audience groups** — each audience sees a different subset of reports/dashboards
4. Map Azure AD security groups to audiences
5. Set default landing page per audience
6. **Publish the app**

Update the app (not create a new one) when content changes after future promotions.

### 8. Validate End-to-End

After the first full deployment:

- Verify the app is accessible to target users
- Confirm data refreshes successfully in PROD with the production database
- Check that RLS filters data correctly for each security role
- Verify each audience sees only their assigned content
- Test the promotion pipeline by making a small change in DEV and promoting it through

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

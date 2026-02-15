#!/usr/bin/env bash
# BigQuery Environment Setup
# ===========================
# This script sets up service accounts and project-level IAM bindings
# for a BigQuery data warehouse.
#
# BigQuery maps to the security model as follows:
#   - Databases      → Datasets (or separate GCP projects for stronger isolation)
#   - Schemas        → Dataset naming convention encodes layer + source
#   - Roles          → IAM custom roles or Google Groups
#   - Warehouses     → On-demand or slot-based pricing (no per-role compute)
#   - Future grants  → IAM bindings at dataset level apply to all tables
#   - Role hierarchy → Google Groups can be nested
#
# No datasets are created in this script — they are all created at runtime:
#   - Raw datasets: created by the ingestion tool (dlt, Fivetran, etc.)
#   - Analytics datasets: created by dbt (analytics_staging, analytics_marts, etc.)
#
# The order of operations problem:
#   BigQuery dataset-level IAM bindings require the dataset to exist. Since dbt
#   creates analytics datasets at runtime, per-dataset grants must be applied
#   after the first dbt run. The grant_usage_on_schemas_where_select on-run-end
#   hook handles this for analyst access. Developer/automation access is handled
#   via project-level IAM roles.
#
# For stronger raw vs analytics isolation, use separate GCP projects
# and grant cross-project access. This script uses a single project
# with dataset-level separation for simplicity.
#
# Sections:
#   1. Variables
#   2. Service accounts
#   3. Project-level IAM bindings

set -euo pipefail

# ============================================================================
# 1. Variables
# ============================================================================

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID environment variable}"

# Google Groups — create these in Google Workspace admin console first
# These act as the role equivalents
GROUP_DEVELOPER="grp-developer@yourdomain.com"   # Google Group
GROUP_ANALYST="grp-analyst@yourdomain.com"        # Google Group

# ============================================================================
# 2. Service Accounts
# ============================================================================
# Create service accounts for loader and automation.
# Human roles (developer, analyst) use Google Groups.

echo "Creating service accounts..."

gcloud iam service-accounts create loader \
  --display-name="Data Loader" \
  --description="Service account for data ingestion (dlt, Fivetran, etc)" \
  --project="$PROJECT_ID" 2>/dev/null || true

gcloud iam service-accounts create automation \
  --display-name="dbt Automation" \
  --description="Service account for dbt CI/CD" \
  --project="$PROJECT_ID" 2>/dev/null || true

LOADER_SA="loader@${PROJECT_ID}.iam.gserviceaccount.com"
AUTOMATION_SA="automation@${PROJECT_ID}.iam.gserviceaccount.com"

# ============================================================================
# 3. Project-level IAM Bindings
# ============================================================================
# BigQuery uses IAM roles at the project or dataset level:
#   - roles/bigquery.dataViewer  → SELECT (read)
#   - roles/bigquery.dataEditor  → INSERT/UPDATE/DELETE + create datasets
#   - roles/bigquery.dataOwner   → Full control including schema changes
#   - roles/bigquery.jobUser     → Run queries
#
# Project-level grants apply to ALL datasets. Fine-grained access (e.g.,
# analyst reads only marts) is handled by dbt's +grants config and the
# grant_usage_on_schemas_where_select on-run-end hook at the dataset level.

echo "Applying project-level IAM bindings..."

# Loader: can create datasets and write data (for raw datasets)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${LOADER_SA}" \
  --role="roles/bigquery.dataEditor" 2>/dev/null || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${LOADER_SA}" \
  --role="roles/bigquery.jobUser" 2>/dev/null || true

# Automation: can create datasets and write data (for analytics datasets)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${AUTOMATION_SA}" \
  --role="roles/bigquery.dataEditor" 2>/dev/null || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${AUTOMATION_SA}" \
  --role="roles/bigquery.jobUser" 2>/dev/null || true

# Developer: can read all datasets and run queries
# Write access to analytics_dev datasets is granted at the dataset level
# after dbt creates them (or via a follow-up script).
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="group:${GROUP_DEVELOPER}" \
  --role="roles/bigquery.dataViewer" 2>/dev/null || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="group:${GROUP_DEVELOPER}" \
  --role="roles/bigquery.jobUser" 2>/dev/null || true

# Analyst: dataset-level grants only (handled by dbt +grants and on-run-end hook)
# Project-level jobUser so they can run queries
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="group:${GROUP_ANALYST}" \
  --role="roles/bigquery.jobUser" 2>/dev/null || true

echo ""
echo "BigQuery setup complete."
echo ""
echo "Notes:"
echo "  - Create Google Groups (grp-developer, grp-analyst) in Workspace admin"
echo "  - Add human users to the appropriate group"
echo "  - Analyst dataset-level access is managed by dbt's +grants config"
echo "  - Developer write access to analytics_dev datasets is granted after"
echo "    dbt creates them (dataset-level dataEditor binding)"
echo "  - For stronger isolation, move raw datasets to a separate GCP project"
echo "    and grant cross-project bigquery.dataViewer to the developer group"

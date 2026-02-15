#!/usr/bin/env bash
# BigQuery Environment Setup
# ===========================
# This script sets up datasets and IAM bindings for a BigQuery data warehouse.
#
# BigQuery maps to the security model as follows:
#   - Databases      → Datasets (or separate GCP projects for stronger isolation)
#   - Schemas        → Dataset naming convention encodes layer + source
#   - Roles          → IAM custom roles or Google Groups
#   - Warehouses     → On-demand or slot-based pricing (no per-role compute)
#   - Future grants  → IAM bindings at dataset level apply to all tables
#   - Role hierarchy → Google Groups can be nested
#
# Prerequisites:
#   - gcloud CLI authenticated with sufficient permissions
#   - PROJECT_ID set to your GCP project
#
# For stronger raw vs analytics isolation, use separate GCP projects
# and grant cross-project access. This script uses a single project
# with dataset-level separation for simplicity.
#
# Sections:
#   1. Variables
#   2. Datasets
#   3. Google Groups (IAM)
#   4. Dataset-level IAM bindings

set -euo pipefail

# ============================================================================
# 1. Variables
# ============================================================================

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID environment variable}"
REGION="${REGION:-US}"

# Google Groups — create these in Google Workspace admin console first
# These act as the role equivalents
GROUP_LOADER="loader@${PROJECT_ID}.iam.gserviceaccount.com"      # service account
GROUP_AUTOMATION="automation@${PROJECT_ID}.iam.gserviceaccount.com"  # service account
GROUP_DEVELOPER="grp-developer@yourdomain.com"                    # Google Group
GROUP_ANALYST="grp-analyst@yourdomain.com"                        # Google Group

# ============================================================================
# 2. Datasets
# ============================================================================
# Dataset naming encodes both the database and schema layer.
# Pattern: <database>_<schema> or <database>_<source> for raw.

echo "Creating datasets..."

# Raw datasets are NOT created here — the ingestion tool (dlt, Fivetran, etc.)
# creates them at runtime. Dataset names are determined by the ingestion tool,
# typically using the pattern: raw_<source> (e.g., raw_hubspot, raw_stripe).
#
# After a raw dataset is created, grant access to the developer group:
#   bq add-iam-policy-binding \
#     --member="group:${GROUP_DEVELOPER}" \
#     --role="roles/bigquery.dataViewer" \
#     "${PROJECT_ID}:raw_<source>"

# Analytics datasets
bq mk --dataset --location="$REGION" --description="Staging layer — cleaned source data" \
  "${PROJECT_ID}:analytics_staging"
bq mk --dataset --location="$REGION" --description="Intermediate layer — business logic joins" \
  "${PROJECT_ID}:analytics_intermediate"
bq mk --dataset --location="$REGION" --description="Marts layer — consumer-facing models" \
  "${PROJECT_ID}:analytics_marts"

# Analytics dev datasets
bq mk --dataset --location="$REGION" --description="Dev staging layer" \
  "${PROJECT_ID}:analytics_dev_staging"
bq mk --dataset --location="$REGION" --description="Dev intermediate layer" \
  "${PROJECT_ID}:analytics_dev_intermediate"
bq mk --dataset --location="$REGION" --description="Dev marts layer" \
  "${PROJECT_ID}:analytics_dev_marts"

# ============================================================================
# 3. Google Groups / Service Accounts
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

# ============================================================================
# 4. Dataset-level IAM Bindings
# ============================================================================
# BigQuery uses IAM roles at the dataset level:
#   - roles/bigquery.dataViewer  → SELECT (read)
#   - roles/bigquery.dataEditor  → INSERT/UPDATE/DELETE (read/write)
#   - roles/bigquery.dataOwner   → Full control including schema changes

echo "Applying IAM bindings..."

# --- Loader: project-level dataEditor for creating datasets ---
# The loader service account needs project-level permissions to create datasets.
# Individual dataset grants are applied after the ingestion tool creates them.
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${GROUP_LOADER}" \
  --role="roles/bigquery.dataEditor" \
  2>/dev/null || true

# --- Analyst: read marts only ---
for dataset in analytics_marts; do
  bq add-iam-policy-binding \
    --member="group:${GROUP_ANALYST}" \
    --role="roles/bigquery.dataViewer" \
    "${PROJECT_ID}:${dataset}" 2>/dev/null || true
done

# --- Developer: read analytics (prod), read/write analytics_dev ---
# Raw dataset grants are applied after the ingestion tool creates them (see above).
for dataset in analytics_staging analytics_intermediate analytics_marts; do
  bq add-iam-policy-binding \
    --member="group:${GROUP_DEVELOPER}" \
    --role="roles/bigquery.dataViewer" \
    "${PROJECT_ID}:${dataset}" 2>/dev/null || true
done

for dataset in analytics_dev_staging analytics_dev_intermediate analytics_dev_marts; do
  bq add-iam-policy-binding \
    --member="group:${GROUP_DEVELOPER}" \
    --role="roles/bigquery.dataEditor" \
    "${PROJECT_ID}:${dataset}" 2>/dev/null || true
done

# --- Automation: read/write analytics (prod) ---
# Raw dataset read grants are applied after the ingestion tool creates them.
for dataset in analytics_staging analytics_intermediate analytics_marts; do
  bq add-iam-policy-binding \
    --member="serviceAccount:${GROUP_AUTOMATION}" \
    --role="roles/bigquery.dataEditor" \
    "${PROJECT_ID}:${dataset}" 2>/dev/null || true
done

echo "BigQuery setup complete."
echo ""
echo "Notes:"
echo "  - Create Google Groups (grp-developer, grp-analyst) in Workspace admin"
echo "  - Add human users to the appropriate group"
echo "  - For per-developer dbt schemas, create datasets like analytics_dev_dbt_jsmith"
echo "    and grant dataEditor to the individual user or developer group"
echo "  - For stronger isolation, move raw datasets to a separate GCP project"
echo "    and grant cross-project bigquery.dataViewer to the developer group"

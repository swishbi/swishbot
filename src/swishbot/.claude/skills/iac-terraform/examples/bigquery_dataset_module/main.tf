# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Example Terraform module: BigQuery dataset with IAM bindings.
# Adapt provider version constraints and resource arguments to the target project.

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

locals {
  common_tags = merge(var.labels, {
    environment = var.environment
    managed_by  = "terraform"
  })
}

# --- Dataset ---

resource "google_bigquery_dataset" "analytics" {
  project                    = var.project_id
  dataset_id                 = "${var.environment}_${var.dataset_id}"
  location                   = var.location
  delete_contents_on_destroy = false
  labels                     = local.common_tags
}

# --- IAM ---
# Grant dataEditor to the automation service account (dbt / dlt).
# Grant dataViewer to the developer group for read access.

resource "google_bigquery_dataset_iam_member" "editor" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${var.automation_sa}"
}

resource "google_bigquery_dataset_iam_member" "viewer" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "group:${var.developer_group}"
}

# --- Outputs ---

output "dataset_id" {
  value       = google_bigquery_dataset.analytics.dataset_id
  description = "Fully qualified dataset ID"
}

output "dataset_self_link" {
  value       = google_bigquery_dataset.analytics.self_link
  description = "Self link for the dataset"
}

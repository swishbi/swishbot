# Copyright (c) 2026 Swish BI Limited. All rights reserved.

variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "dataset_id" {
  type        = string
  description = "Base dataset ID (environment prefix added automatically)"
}

variable "location" {
  type        = string
  default     = "US"
  description = "BigQuery dataset location"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

variable "automation_sa" {
  type        = string
  description = "Service account email for automation (dbt, dlt) — receives dataEditor"
}

variable "developer_group" {
  type        = string
  description = "Google group email for developers — receives dataViewer"
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Additional labels to apply to the dataset"
}

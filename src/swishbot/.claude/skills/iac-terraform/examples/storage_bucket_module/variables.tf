# Copyright (c) 2026 Swish BI Limited. All rights reserved.

variable "cloud_provider" {
  type        = string
  description = "Cloud provider for the bucket: 'gcs' or 's3'"

  validation {
    condition     = contains(["gcs", "s3"], var.cloud_provider)
    error_message = "cloud_provider must be 'gcs' or 's3'."
  }
}

variable "bucket_name" {
  type        = string
  description = "Base bucket name (environment prefix added automatically)"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

variable "region" {
  type        = string
  description = "Cloud region for the bucket"
}

variable "project_id" {
  type        = string
  default     = ""
  description = "GCP project ID (required for GCS, ignored for S3)"
}

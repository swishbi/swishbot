# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Example Terraform module: Cloud storage bucket (GCS or S3).
# Uses var.cloud_provider to select the correct resource type.
# Adapt provider version constraints and resource arguments to the target project.

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  is_gcs = var.cloud_provider == "gcs"
  is_s3  = var.cloud_provider == "s3"
}

# --- GCS Bucket ---

resource "google_storage_bucket" "data" {
  count = local.is_gcs ? 1 : 0

  project                     = var.project_id
  name                        = "${var.environment}-${var.bucket_name}"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# --- S3 Bucket ---

resource "aws_s3_bucket" "data" {
  count = local.is_s3 ? 1 : 0

  bucket        = "${var.environment}-${var.bucket_name}"
  force_destroy = false

  tags = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "data" {
  count  = local.is_s3 ? 1 : 0
  bucket = aws_s3_bucket.data[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  count  = local.is_s3 ? 1 : 0
  bucket = aws_s3_bucket.data[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data" {
  count  = local.is_s3 ? 1 : 0
  bucket = aws_s3_bucket.data[0].id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
  }
}

# --- Outputs ---

output "bucket_name" {
  value       = local.is_gcs ? google_storage_bucket.data[0].name : (local.is_s3 ? aws_s3_bucket.data[0].id : null)
  description = "Bucket name"
}

output "bucket_url" {
  value       = local.is_gcs ? google_storage_bucket.data[0].url : (local.is_s3 ? "s3://${aws_s3_bucket.data[0].id}" : null)
  description = "Bucket URL (gs:// or s3://)"
}

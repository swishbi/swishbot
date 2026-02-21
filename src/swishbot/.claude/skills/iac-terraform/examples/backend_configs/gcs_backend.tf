# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Partial backend configuration for Google Cloud Storage.
# Pass credentials via GOOGLE_CREDENTIALS env var or Workload Identity.
# Pass bucket name at init:
#   terraform init -backend-config="bucket=my-tfstate-bucket"

terraform {
  backend "gcs" {
    prefix = "prod/terraform"
  }
}

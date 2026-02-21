# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Partial backend configuration for AWS S3.
# Pass credentials and bucket name via environment variables at init:
#   terraform init \
#     -backend-config="bucket=my-tfstate-bucket" \
#     -backend-config="access_key=$AWS_ACCESS_KEY_ID" \
#     -backend-config="secret_key=$AWS_SECRET_ACCESS_KEY"

terraform {
  backend "s3" {
    region         = "us-east-1"
    key            = "prod/terraform.tfstate"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}

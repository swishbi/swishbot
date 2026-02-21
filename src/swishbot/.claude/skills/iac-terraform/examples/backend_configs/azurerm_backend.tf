# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Partial backend configuration for Azure Blob Storage.
# Pass credentials via ARM_CLIENT_ID and ARM_CLIENT_SECRET env vars,
# or use Managed Identity.

terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstateaccount"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }
}

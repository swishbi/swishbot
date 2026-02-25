# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Example Terraform module: Snowflake warehouse + database provisioning.
# Adapt provider version constraints and resource arguments to the target project.

terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 1.0"
    }
  }
}

# --- Warehouse ---

resource "snowflake_warehouse" "analytics" {
  name                = "${var.environment}_${var.warehouse_name}"
  warehouse_size      = var.warehouse_size
  auto_suspend        = var.auto_suspend
  auto_resume         = true
  initially_suspended = true
  warehouse_type      = "STANDARD"
}

# --- Database ---

resource "snowflake_database" "analytics" {
  name = "${upper(var.environment)}_ANALYTICS"
}

# --- Grants ---
# Grant warehouse usage to the automation role so dbt / dlt can run queries.
# Fine-grained schema/table grants are managed by the dba-security skill.

resource "snowflake_grant_privileges_to_account_role" "warehouse_usage" {
  account_role_name = var.automation_role
  privileges        = ["USAGE"]

  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.analytics.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "database_usage" {
  account_role_name = var.automation_role
  privileges        = ["USAGE", "CREATE SCHEMA"]

  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.analytics.name
  }
}

# --- Outputs ---

output "warehouse_name" {
  value       = snowflake_warehouse.analytics.name
  description = "Fully qualified warehouse name"
}

output "database_name" {
  value       = snowflake_database.analytics.name
  description = "Fully qualified database name"
}

# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Example Terraform module: Databricks workspace-level resources.
# This module manages resources INSIDE an existing workspace (groups, policies,
# service principals). The workspace itself is provisioned through the cloud
# provider (azurerm_databricks_workspace, google_databricks_workspace, etc.).
# Adapt provider version constraints and resource arguments to the target project.

terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }
}

# --- Service Principal ---
# Automation identity for dbt / dlt jobs.

resource "databricks_service_principal" "automation" {
  display_name = var.automation_sp_display_name
}

# --- Groups ---

resource "databricks_group" "loaders" {
  display_name = "${var.environment}_loaders"
}

resource "databricks_group" "developers" {
  display_name = "${var.environment}_developers"
}

resource "databricks_group" "automation" {
  display_name = "${var.environment}_automation"
}

resource "databricks_group_member" "automation_sp" {
  group_id  = databricks_group.automation.id
  member_id = databricks_service_principal.automation.id
}

# --- Cluster Policy ---
# Restrict cluster sizes to control costs.

resource "databricks_cluster_policy" "default" {
  name = "${var.environment}_default_policy"

  definition = jsonencode({
    "dbus_per_hour" : {
      "type" : "range",
      "maxValue" : var.max_cluster_dbu_per_hour
    },
    "autotermination_minutes" : {
      "type" : "fixed",
      "value" : 30
    },
    "custom_tags.environment" : {
      "type" : "fixed",
      "value" : var.environment
    },
    "custom_tags.managed_by" : {
      "type" : "fixed",
      "value" : "terraform"
    }
  })
}

# --- Outputs ---

output "automation_sp_id" {
  value       = databricks_service_principal.automation.id
  description = "Service principal ID for automation"
}

output "cluster_policy_id" {
  value       = databricks_cluster_policy.default.id
  description = "Default cluster policy ID"
}

output "group_ids" {
  value = {
    loaders    = databricks_group.loaders.id
    developers = databricks_group.developers.id
    automation = databricks_group.automation.id
  }
  description = "Map of group names to IDs"
}

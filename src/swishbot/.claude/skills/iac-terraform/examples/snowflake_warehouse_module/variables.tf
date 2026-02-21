# Copyright (c) 2026 Swish BI Limited. All rights reserved.

variable "warehouse_name" {
  type        = string
  description = "Base name for the warehouse (environment prefix added automatically)"
}

variable "warehouse_size" {
  type        = string
  default     = "XSMALL"
  description = "Snowflake warehouse size (XSMALL, SMALL, MEDIUM, LARGE, etc.)"
}

variable "auto_suspend" {
  type        = number
  default     = 600
  description = "Seconds of inactivity before the warehouse auto-suspends"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

variable "automation_role" {
  type        = string
  description = "Snowflake role for automation (dbt, dlt) — receives USAGE grants"
}

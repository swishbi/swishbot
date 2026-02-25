# Copyright (c) 2026 Swish BI Limited. All rights reserved.

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

variable "automation_sp_display_name" {
  type        = string
  default     = "svc_automation"
  description = "Display name for the automation service principal"
}

variable "max_cluster_dbu_per_hour" {
  type        = number
  default     = 10
  description = "Maximum DBUs per hour allowed by the default cluster policy"
}

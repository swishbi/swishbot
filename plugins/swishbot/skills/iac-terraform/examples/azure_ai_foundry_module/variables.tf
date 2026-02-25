# Copyright (c) 2026 Swish BI Limited. All rights reserved.

# --- General ---

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

variable "location" {
  type        = string
  default     = "eastus2"
  description = "Azure region for the Foundry resource"
}

variable "resource_name_prefix" {
  type        = string
  default     = "aifoundry"
  description = "Prefix for the Foundry resource name (a random suffix is appended for uniqueness)"
}

variable "tags" {
  type = map(string)
  default = {
    managed_by = "terraform"
  }
  description = "Tags applied to all resources"
}

# --- Project ---

variable "project_name" {
  type        = string
  default     = "analytics"
  description = "AI Foundry project name"
}

variable "project_description" {
  type        = string
  default     = "Data engineering and analytics project"
  description = "AI Foundry project description"
}

# --- Authentication ---

variable "disable_api_key_auth" {
  type        = bool
  default     = false
  description = "Set true to disable API key auth and require Entra ID only"
}

# --- Claude Deployments ---
# Pin specific model versions. Do NOT rely on auto-update — Claude Code may attempt
# to use a newer version that is not yet deployed, breaking existing users.

variable "deployment_sku" {
  type        = string
  default     = "GlobalStandard"
  description = "SKU for Claude deployments (GlobalStandard or ProvisionedManaged)"
}

variable "deploy_opus" {
  type        = bool
  default     = true
  description = "Whether to deploy Claude Opus (recommended for complex tasks)"
}

variable "opus_deployment_name" {
  type        = string
  default     = "claude-opus-4-6"
  description = "Deployment name for Claude Opus"
}

variable "opus_model_id" {
  type        = string
  default     = "claude-opus-4-6"
  description = "Model ID for Claude Opus — pin to a specific version"
}

variable "opus_model_version" {
  type        = string
  default     = "2025-09-25"
  description = "Model version for Claude Opus"
}

variable "opus_capacity" {
  type        = number
  default     = 1
  description = "Capacity units for the Opus deployment"
}

variable "sonnet_deployment_name" {
  type        = string
  default     = "claude-sonnet-4-6"
  description = "Deployment name for Claude Sonnet"
}

variable "sonnet_model_id" {
  type        = string
  default     = "claude-sonnet-4-6"
  description = "Model ID for Claude Sonnet — pin to a specific version"
}

variable "sonnet_model_version" {
  type        = string
  default     = "2025-09-25"
  description = "Model version for Claude Sonnet"
}

variable "sonnet_capacity" {
  type        = number
  default     = 1
  description = "Capacity units for the Sonnet deployment"
}

variable "deploy_haiku" {
  type        = bool
  default     = true
  description = "Whether to deploy Claude Haiku (recommended for fast mode)"
}

variable "haiku_deployment_name" {
  type        = string
  default     = "claude-haiku-4-5"
  description = "Deployment name for Claude Haiku"
}

variable "haiku_model_id" {
  type        = string
  default     = "claude-haiku-4-5"
  description = "Model ID for Claude Haiku — pin to a specific version"
}

variable "haiku_model_version" {
  type        = string
  default     = "2024-10-01"
  description = "Model version for Claude Haiku"
}

variable "haiku_capacity" {
  type        = number
  default     = 1
  description = "Capacity units for the Haiku deployment"
}

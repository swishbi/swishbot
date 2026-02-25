# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Example Terraform module: Azure AI Foundry with Claude deployments.
# Provisions a Microsoft Foundry resource, project, and Claude model deployments
# so that Claude Code can be used within a client's Azure tenant.
#
# Supports both AzAPI and AzureRM providers. This example uses AzAPI for full
# control plane access including preview features and connection configuration.
#
# After provisioning, configure Claude Code on each workstation:
#   export CLAUDE_CODE_USE_FOUNDRY=1
#   export ANTHROPIC_FOUNDRY_RESOURCE=<resource_name>
#   export ANTHROPIC_DEFAULT_OPUS_MODEL='claude-opus-4-6'
#   export ANTHROPIC_DEFAULT_SONNET_MODEL='claude-sonnet-4-6'
#   export ANTHROPIC_DEFAULT_HAIKU_MODEL='claude-haiku-4-5'
#
# Authentication: either set ANTHROPIC_FOUNDRY_API_KEY or use Entra ID (az login).
# See: https://code.claude.com/docs/en/microsoft-foundry

terraform {
  required_providers {
    azapi = {
      source  = "azure/azapi"
      version = "~> 2.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# --- Random suffix for globally unique names ---

resource "random_string" "unique" {
  length      = 5
  min_numeric = 5
  numeric     = true
  special     = false
  lower       = true
  upper       = false
}

# --- Resource Group ---

resource "azurerm_resource_group" "foundry" {
  name     = "rg-${var.environment}-aifoundry-${random_string.unique.result}"
  location = var.location

  tags = var.tags
}

# --- AI Foundry Resource ---
# Uses AzAPI for full control plane access (connections, capability hosts, preview features).
# Set allowProjectManagement = true to enable project creation.

resource "azapi_resource" "ai_foundry" {
  type                      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name                      = "${var.resource_name_prefix}${random_string.unique.result}"
  parent_id                 = azurerm_resource_group.foundry.id
  location                  = var.location
  schema_validation_enabled = false

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }

    properties = {
      # Support both Entra ID and API Key authentication
      disableLocalAuth = var.disable_api_key_auth

      # Enable project management (required for AI Foundry)
      allowProjectManagement = true

      # Custom subdomain for the Foundry endpoint URL
      customSubDomainName = "${var.resource_name_prefix}${random_string.unique.result}"
    }
  }

  tags = var.tags
}

# --- AI Foundry Project ---
# Projects are folders for organising stateful work (agents, threads, deployments).

resource "azapi_resource" "project" {
  type                      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name                      = "${var.environment}-${var.project_name}"
  parent_id                 = azapi_resource.ai_foundry.id
  location                  = var.location
  schema_validation_enabled = false

  body = {
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }

    properties = {
      displayName = "${var.project_name} (${var.environment})"
      description = var.project_description
    }
  }
}

# --- Claude Model Deployments ---
# Pin specific model versions — do NOT use auto-update or aliases.
# Claude Code requires at minimum a Sonnet deployment. Opus and Haiku are optional
# but recommended for full functionality (Opus for complex tasks, Haiku for fast mode).

resource "azapi_resource" "claude_opus" {
  count     = var.deploy_opus ? 1 : 0
  type      = "Microsoft.CognitiveServices/accounts/deployments@2023-05-01"
  name      = var.opus_deployment_name
  parent_id = azapi_resource.ai_foundry.id

  depends_on = [azapi_resource.ai_foundry]

  body = {
    sku = {
      name     = var.deployment_sku
      capacity = var.opus_capacity
    }
    properties = {
      model = {
        format  = "Anthropic"
        name    = var.opus_model_id
        version = var.opus_model_version
      }
    }
  }
}

resource "azapi_resource" "claude_sonnet" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2023-05-01"
  name      = var.sonnet_deployment_name
  parent_id = azapi_resource.ai_foundry.id

  depends_on = [
    azapi_resource.ai_foundry,
    azapi_resource.claude_opus
  ]

  body = {
    sku = {
      name     = var.deployment_sku
      capacity = var.sonnet_capacity
    }
    properties = {
      model = {
        format  = "Anthropic"
        name    = var.sonnet_model_id
        version = var.sonnet_model_version
      }
    }
  }
}

resource "azapi_resource" "claude_haiku" {
  count     = var.deploy_haiku ? 1 : 0
  type      = "Microsoft.CognitiveServices/accounts/deployments@2023-05-01"
  name      = var.haiku_deployment_name
  parent_id = azapi_resource.ai_foundry.id

  depends_on = [
    azapi_resource.ai_foundry,
    azapi_resource.claude_sonnet
  ]

  body = {
    sku = {
      name     = var.deployment_sku
      capacity = var.haiku_capacity
    }
    properties = {
      model = {
        format  = "Anthropic"
        name    = var.haiku_model_id
        version = var.haiku_model_version
      }
    }
  }
}

# --- Outputs ---

output "resource_group_name" {
  value       = azurerm_resource_group.foundry.name
  description = "Resource group containing the Foundry resource"
}

output "foundry_resource_name" {
  value       = azapi_resource.ai_foundry.name
  description = "AI Foundry resource name — use as ANTHROPIC_FOUNDRY_RESOURCE"
}

output "foundry_endpoint" {
  value       = "https://${azapi_resource.ai_foundry.name}.services.ai.azure.com/anthropic"
  description = "AI Foundry endpoint URL — use as ANTHROPIC_FOUNDRY_BASE_URL"
}

output "project_name" {
  value       = azapi_resource.project.name
  description = "AI Foundry project name"
}

output "claude_code_env_vars" {
  value = <<-EOT
    # Claude Code configuration for this Foundry resource
    export CLAUDE_CODE_USE_FOUNDRY=1
    export ANTHROPIC_FOUNDRY_RESOURCE=${azapi_resource.ai_foundry.name}
    export ANTHROPIC_DEFAULT_OPUS_MODEL='${var.opus_model_id}'
    export ANTHROPIC_DEFAULT_SONNET_MODEL='${var.sonnet_model_id}'
    export ANTHROPIC_DEFAULT_HAIKU_MODEL='${var.haiku_model_id}'
  EOT
  description = "Environment variables to configure Claude Code for this Foundry resource"
}

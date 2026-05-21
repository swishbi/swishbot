---
name: iac-terraform
description: "Deploy analytics infrastructure as code with Terraform. Use when a user asks to provision Snowflake warehouses, BigQuery datasets, Databricks workspaces, GCS/S3 storage buckets, IAM roles, or Azure AI Foundry resources for data platform services."
---

# Infrastructure as Code — Terraform

## Overview

Infrastructure is **declarative** — define the desired end state in `.tf` files, let Terraform converge to it. The goal is repeatable, auditable provisioning with no manual console clicks.

Four principles govern every Terraform project:

1. **Modules for reuse** — one module per resource type (warehouse, storage, IAM); never a monolith "everything" module
2. **Remote state for collaboration** — local `.tfstate` files break team workflows and CI/CD
3. **Environment parity** — dev, staging, and prod use the same modules with different variable values
4. **Least privilege** — service accounts get the minimum IAM bindings required; no wildcard grants

The data platform maps to four infrastructure layers:

| Layer | Terraform Resources | Example |
|-------|-------------------|---------|
| **Compute** | Warehouses, clusters, workspaces | `snowflake_warehouse`, `databricks_cluster_policy` |
| **Storage** | Buckets, datasets, databases | `google_storage_bucket`, `aws_s3_bucket`, `snowflake_database` |
| **Networking** | VPCs, private endpoints, firewall rules | `google_compute_network`, `aws_vpc` |
| **IAM** | Roles, service accounts, bindings | `google_project_iam_member`, `snowflake_grant_privileges_to_account_role` |
| **AI Services** | Foundry resources, model deployments, projects | `azapi_resource` (Microsoft.CognitiveServices/accounts) |

Provision infrastructure first, then hand off to dba-security for warehouse-level roles and grants.

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Set Up Project Structure](workflows/setup-project-structure.md) | Starting from scratch — directory layout, modules, providers, local validation |
| [Configure Environments, State & CI/CD](workflows/configure-environments-state-cicd.md) | Remote backends, environment isolation, variable strategy, deployment pipelines |

## Anti-Patterns

- **Inline credentials in `.tf` files** — use environment variables or a secrets manager; never commit secrets
- **Single workspace for all environments** — environments must be isolated by directory or workspace to prevent cross-contamination
- **Hardcoded resource names** — use variables and naming conventions so modules are reusable across environments
- **`terraform apply` without a plan review gate** — always run `plan` first; require approval for production applies
- **Running `terraform destroy` on shared infrastructure** — always requires explicit user confirmation
- **God modules** — one module per resource type; a single module provisioning warehouses, buckets, and IAM together is unmaintainable
- **No remote state** — local state breaks team collaboration and CI/CD; always configure a remote backend

## Related Skills

- **[dba-security](../dba-security/SKILL.md)** — Warehouse roles, grants, and access controls applied after infrastructure is provisioned
- **[dlt](../dlt/SKILL.md)** — Ingestion pipelines that write to the storage buckets and databases Terraform provisions
- **[dagster](../dagster/SKILL.md)** — Orchestration infrastructure (service accounts, secrets, compute) provisioned by Terraform

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

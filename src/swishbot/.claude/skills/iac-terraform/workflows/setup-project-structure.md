# Set Up Terraform Project Structure

Bootstrap a Terraform project for data infrastructure with a module-based layout, provider configuration, and local validation.

## Step 1: Create the Directory Layout

Organise the project into two top-level concerns: **modules** (reusable resource definitions) and **environments** (per-environment configuration that calls modules).

```
terraform/
├── modules/
│   ├── snowflake_warehouse/    # Warehouse + database provisioning
│   ├── bigquery_dataset/       # BigQuery dataset + IAM bindings
│   ├── storage_bucket/         # GCS or S3 bucket with lifecycle rules
│   ├── databricks_workspace/   # Workspace-level resources (groups, policies)
│   ├── azure_ai_foundry/       # AI Foundry resource + Claude deployments
│   └── iam/                    # Cross-cutting IAM bindings (optional)
├── environments/
│   ├── dev/
│   │   ├── main.tf             # Module calls with dev-specific inputs
│   │   ├── variables.tf        # Variable declarations
│   │   ├── terraform.tfvars    # Non-secret variable values
│   │   └── backend.tf          # Remote state config for dev
│   ├── staging/
│   │   └── ...                 # Same structure as dev
│   └── prod/
│       └── ...                 # Same structure as dev
└── README.md
```

This separation ensures modules contain **zero** environment-specific values. Every string that varies per environment is a variable, passed in by the environment caller.

## Step 2: Write the Module Pattern

Each module follows a canonical three-file structure: `main.tf` (resources), `variables.tf` (inputs), `outputs.tf` (exports).

A module's `main.tf` starts with the `terraform` block declaring required providers:

```hcl
terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 1.0"
    }
  }
}
```

Provider version constraints by platform:

| Platform | Provider source | Recommended constraint |
|----------|----------------|----------------------|
| Snowflake | `Snowflake-Labs/snowflake` | `~> 1.0` |
| BigQuery / GCS | `hashicorp/google` | `~> 6.0` |
| Databricks | `databricks/databricks` | `~> 1.0` |
| AWS (S3, IAM) | `hashicorp/aws` | `~> 5.0` |
| Azure | `hashicorp/azurerm` | `~> 4.0` |
| Azure (AzAPI) | `azure/azapi` | `~> 2.0` |

Key rules for modules:
- No hardcoded values — every configurable string is a `variable`
- No `provider` blocks inside modules — providers are configured by the environment caller
- Every resource the downstream needs is exported via `output`
- One module per resource type — never a "god module" provisioning everything

## Step 3: Configure the Environment Caller

Each environment directory calls modules with environment-specific values. The `main.tf` in `environments/prod/` wires modules together:

```hcl
module "warehouse" {
  source          = "../../modules/snowflake_warehouse"
  warehouse_name  = var.warehouse_name
  warehouse_size  = var.warehouse_size
  auto_suspend    = var.auto_suspend
  environment     = var.environment
  automation_role = var.automation_role
}
```

The `terraform.tfvars` file supplies non-secret values:

```hcl
environment     = "prod"
warehouse_name  = "analytics_wh"
warehouse_size  = "MEDIUM"
auto_suspend    = 300
automation_role = "svc_transformer"
```

Secret values (API keys, passwords, service account keys) are **never** stored in `.tfvars`. Pass them via `TF_VAR_*` environment variables at runtime, sourced from the CI secret store.

## Step 4: Reference Platform-Specific Examples

Working module examples are available for each supported platform:

| Module | Resources | Example path |
|--------|-----------|-------------|
| Snowflake warehouse | Warehouse, database, role grants | `examples/snowflake_warehouse_module/` |
| BigQuery dataset | Dataset, IAM member bindings | `examples/bigquery_dataset_module/` |
| Storage bucket | GCS/S3 bucket with versioning and lifecycle | `examples/storage_bucket_module/` |
| Databricks workspace | Cluster policy, groups, service principal | `examples/databricks_workspace_module/` |
| Azure AI Foundry | Foundry resource, project, Claude model deployments | `examples/azure_ai_foundry_module/` |

These are reference modules — review provider version constraints and adapt resource arguments to the target project before use.

**Note on Databricks:** The Databricks provider manages workspace-level resources (groups, service principals, cluster policies). The workspace itself is provisioned through the cloud provider (`azurerm_databricks_workspace`, `google_databricks_workspace`, or `aws_databricks_workspace`).

**Note on Azure AI Foundry:** The example uses the AzAPI provider for full control plane access. It provisions a Foundry resource with Claude Opus, Sonnet, and Haiku deployments — pin specific model versions to prevent breakage when new models are released. After provisioning, configure Claude Code on each workstation with the environment variables shown in the module's `claude_code_env_vars` output. Authentication supports both API key (`ANTHROPIC_FOUNDRY_API_KEY`) and Entra ID (`az login`). See [Claude Code on Microsoft Foundry](https://code.claude.com/docs/en/microsoft-foundry) for full setup details.

## Step 5: Validate Locally

Run the standard validation sequence before pushing:

```bash
terraform init          # Download providers and initialise backend
terraform validate      # Check syntax and internal consistency
terraform plan          # Preview changes — review before applying
```

Check the plan output for:
- No hardcoded secrets visible in resource arguments
- All resource names follow the `<env>_<resource>` naming convention
- Provider versions match the constraints in Step 2

The `scripts/validate-terraform.sh` hook automatically blocks `terraform destroy` and other destructive commands, requiring explicit user confirmation.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

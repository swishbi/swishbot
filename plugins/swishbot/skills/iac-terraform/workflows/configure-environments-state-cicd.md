# Configure Environments, State & CI/CD

Configure remote state backends, per-environment isolation, variable strategy, and CI/CD pipeline gating for safe Terraform deployments.

## Step 1: Choose and Configure the Remote Backend

Local `.tfstate` files are a single point of failure and block team collaboration. Always configure a remote backend with state locking.

| Cloud | Backend type | State locking | Example file |
|-------|-------------|--------------|-------------|
| AWS | S3 + DynamoDB | DynamoDB table | `examples/backend_configs/s3_backend.tf` |
| GCP | GCS | Built-in | `examples/backend_configs/gcs_backend.tf` |
| Azure | Azure Blob Storage | Built-in lease | `examples/backend_configs/azurerm_backend.tf` |
| Cross-cloud | Terraform Cloud | Built-in | `terraform { cloud {} }` block |

A concrete S3 backend configuration:

```hcl
terraform {
  backend "s3" {
    region         = "us-east-1"
    key            = "prod/terraform.tfstate"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}
```

Key rule: use **partial configuration** — do not put credentials or bucket names in `backend.tf`. Pass them at init time:

```bash
terraform init \
  -backend-config="bucket=my-tfstate-bucket" \
  -backend-config="access_key=$AWS_ACCESS_KEY_ID" \
  -backend-config="secret_key=$AWS_SECRET_ACCESS_KEY"
```

## Step 2: Isolate Environments

Two strategies exist for environment isolation. Directory-per-environment is recommended for data platform projects.

| Strategy | Isolation | State separation | Trade-off |
|----------|-----------|-----------------|-----------|
| **Directory-per-env** (recommended) | Strong — each env is a separate Terraform root | Separate state file per directory | More files, but explicit and auditable |
| **Workspaces** | Moderate — same root, different state | Workspace-namespaced state in same backend | Less duplication, but easy to `apply` in wrong workspace |

With directory-per-environment, each `environments/<env>/backend.tf` points to a different state key:

- `environments/dev/backend.tf` → `key = "dev/terraform.tfstate"`
- `environments/staging/backend.tf` → `key = "staging/terraform.tfstate"`
- `environments/prod/backend.tf` → `key = "prod/terraform.tfstate"`

Production state bucket requirements:
- **Versioning enabled** — recover from accidental state corruption
- **Deletion protection** — prevent accidental bucket deletion
- **Encryption at rest** — state files contain sensitive resource metadata

## Step 3: Configure Per-Environment Variables

Three tiers of variable configuration, from least sensitive to most:

| Tier | Mechanism | Example values | Committed to git? |
|------|-----------|---------------|-------------------|
| **Static config** | `terraform.tfvars` | Warehouse size, region, tags, environment name | Yes |
| **Secrets** | `TF_VAR_*` env vars | API keys, passwords, service account JSON | No — sourced from CI secret store |
| **Hardcoded in module** | `locals {}` block | Provider source URLs, resource type defaults | Yes (inside module) |

The `terraform.tfvars` file per environment:

```hcl
environment    = "prod"
warehouse_size = "MEDIUM"
region         = "us-east-1"
```

In CI/CD, secrets are injected as environment variables:

```bash
export TF_VAR_snowflake_password="$SNOWFLAKE_PASSWORD"   # from CI secret store
export TF_VAR_gcp_sa_key="$GCP_SA_KEY"                   # from CI secret store
```

Never store `.tfvars` files containing secrets. Add `*.auto.tfvars` to `.gitignore` if using auto-loaded variable files for local development.

## Step 4: Build the CI/CD Pipeline Gate

Use a two-stage pipeline: **plan** on every pull request, **apply** on merge to main. Production applies require manual approval.

```yaml
# GitHub Actions example
name: Terraform
on:
  pull_request:
    paths: ["terraform/**"]
  push:
    branches: [main]
    paths: ["terraform/**"]

jobs:
  plan:
    runs-on: ubuntu-latest
    permissions:
      id-token: write        # OIDC auth to cloud provider
      pull-requests: write   # Comment plan output on PR
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.x"    # Pin the CLI version
      - run: terraform -chdir=terraform/environments/prod init
      - run: terraform -chdir=terraform/environments/prod plan -out=tfplan
      - run: terraform show -no-color tfplan >> $GITHUB_STEP_SUMMARY

  apply:
    if: github.ref == 'refs/heads/main'
    needs: plan
    runs-on: ubuntu-latest
    environment: production          # Requires manual approval
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.x"
      - run: terraform -chdir=terraform/environments/prod init
      - run: terraform -chdir=terraform/environments/prod apply -auto-approve tfplan
```

Key rules:
- **Pin the Terraform CLI version** in CI — prevent drift between local and CI behaviour
- **Use OIDC authentication** to the cloud provider (not long-lived access keys)
- **Never `apply` without a reviewed plan** — the plan job comments output on the PR for review
- **Require manual approval for production** — use GitHub Environments or equivalent gating

## Step 5: Tag Every Resource

Apply a mandatory tagging strategy to every resource for cost allocation and audit:

```hcl
locals {
  common_tags = {
    environment = var.environment
    managed_by  = "terraform"
    repo        = "my-org/data-platform"
    cost_center = var.cost_center
  }
}

module "warehouse" {
  source = "../../modules/snowflake_warehouse"
  tags   = local.common_tags
  # ... other variables
}
```

Required tags:

| Tag | Purpose |
|-----|---------|
| `environment` | Identifies dev/staging/prod for cost and access filtering |
| `managed_by` | Distinguishes Terraform-managed from manually created resources |
| `repo` | Links the resource back to its source code for auditing |
| `cost_center` | Drives cost allocation reporting (optional but recommended) |

Tags are the only reliable way to audit what Terraform manages versus what was created manually. Enforce them in every module's `variables.tf` as a required `map(string)` input.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

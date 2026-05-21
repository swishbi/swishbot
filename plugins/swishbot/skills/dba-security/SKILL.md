---
name: dba-security
description: "Apply DBA security best practices. Use when a user asks to set up warehouse roles, configure access controls, create database environments, set up dbt grants, implement row-level security, or audit permissions. Applies to Snowflake, BigQuery, Databricks, Postgres, and DuckDB."
---

# DBA Security Practices

## Overview

Security is about **separation** — separate layers, databases, environments, and roles. The goal is to limit blast radius and enforce least-privilege access at every level of the warehouse.

The warehouse is organised into 4 layers:

| Layer | Purpose | Schema pattern |
|-------|---------|----------------|
| **Raw** | Unprocessed source data | One schema per source system, created at runtime by the ingestion tool (e.g., `hubspot`, `stripe`) |
| **Staging (bronze)** | First transformation layer — clean, rename, type | `staging` schema |
| **Intermediate (silver)** | Business logic joins and enrichment | `intermediate` schema |
| **Marts (gold)** | Consumer-facing analytical models | `marts` schema (split later as complexity grows) |

Raw schema names are determined by the ingestion tool (dlt, Fivetran, Airbyte, etc.) — typically just the source name (e.g., `hubspot`, `stripe`). The setup scripts grant `CREATE SCHEMA` to the loader role so the ingestion tool can create these at runtime. Do not pre-create raw schemas in the setup scripts.

As mart complexity grows, split into domain-specific schemas (e.g., `mrt_finance`, `mrt_marketing`). This also enables fine-grained analyst roles per domain.

## Workflows

| Workflow | When to Use |
|----------|-------------|
| [Setup Warehouse Security](workflows/setup-warehouse-security.md) | Setting up from scratch — database separation, environments, roles, platform scripts |
| [Configure dbt Security](workflows/configure-dbt-security.md) | Configuring dbt grants, schema resolution, profiles, and hooks |

## Anti-Patterns

- **Single admin role for everything** — no separation of concerns, impossible to audit
- **Giving developers write access to production** — all production writes should go through automation
- **Sharing service account credentials** — each service gets its own user and key pair
- **No environment separation** — development writes hitting production data
- **Granting `SELECT *` on raw to analysts** — raw may contain PII/PHI; analysts should only see the marts layer
- **Using password auth for service accounts** — key-pair auth is more secure and supports rotation

## Related Skills

- **[iac-terraform](../iac-terraform/SKILL.md)** — Provision the warehouse, databases, and IAM roles that dba-security configures
- **[dlt](../dlt/SKILL.md)** — Loader role and raw database permissions
- **[dbt](../dbt/SKILL.md)** — Staging layer references raw database, first transformed layer in analytics

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

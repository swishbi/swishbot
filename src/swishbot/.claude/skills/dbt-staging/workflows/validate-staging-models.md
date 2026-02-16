# Validate Staging Models

Create model YAML files and run dbt build to verify staging models.

## Step 1: Create Model YAML Files

Create a YAML file for each staging model (both parent and flattened, both active and disabled):

```yaml
version: 2

models:
  - name: stg_<source_name>__<table_name>
    description: ""
```

Create one `.yml` file per `.sql` file, with matching names.

## Step 2: Validate

Build the staging models to verify everything works:

```bash
cd transformation && dbt build --select staging.<source_name>
```

Use the dbt MCP `show` tool to preview results of individual models:

```sql
select * from {{ ref('stg_<source_name>__<table_name>') }} limit 10
```

## Checklist

- [ ] Model YAML file created for each staging model (`.yml` per `.sql`)
- [ ] Loader metadata columns included
- [ ] `dbt build` passes for the new source

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

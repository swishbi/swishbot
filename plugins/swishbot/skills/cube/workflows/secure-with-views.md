# Publish a View and Decide Who Can Query It

Views are the only way consumers reach data. Each consumer group gets the views it needs, through an access policy, and logs in as its own SQL API user.

## Step 1: Decide the Consumers

| Consumer | Typical view | Members |
|----------|--------------|---------|
| BI tool (Metabase, Superset) | `finance_profit_and_loss` | Measures, dimensions, IDs where drill-through needs them |
| AI agent (Claude Code through an SQL MCP) | `agent_profit_and_loss` | Aggregates only: measures and descriptive dimensions, **no IDs, document numbers or names of people** |

One view per consumer and subject. A view's name and its member names are the contract: dashboards, saved questions and agent prompts use them.

## Step 2: Write the View

```yaml
views:
  - name: finance_profit_and_loss
    title: "Profit and loss"
    description: "Monthly P&L by account. The view the BI tool reads."

    access_policy:
      - group: metabase
        row_level:
          allow_all: true

    cubes:
      - join_path: rpt_quickbooks_profit_and_loss
        includes:
          - net_profit
          - month_start
      - join_path: rpt_quickbooks_profit_and_loss.dim_quickbooks_account
        includes:
          - account_id
          - account_name
          - account_type
```

The view exposes exactly the members its `includes` lists. Anything not listed doesn't exist for that consumer.

## Step 3: Keep Public Names Stable

When a mart column is renamed, change the cube member's `sql:` and leave its `name` alone. If a cube member's name must change, alias it in the view so the public name stays:

```yaml
        includes:
          - name: month_start
            alias: report_month
```

## Step 4: Map SQL API Users to Groups

In `cube.js`, `checkSqlAuth` accepts only the consumers you name and returns each one's group; `contextToGroups` exposes that group to the access policies.

```js
const SQL_USERS = {
  metabase: { passwordEnv: 'CUBE_SQL_PASSWORD_METABASE', group: 'metabase' },
  agent:    { passwordEnv: 'CUBE_SQL_PASSWORD_AGENT',    group: 'agent' },
};

module.exports = {
  checkSqlAuth: (request, user) => {
    const entry = SQL_USERS[user];
    if (!entry) throw new Error(`Incorrect user name "${user}" or password`);
    return {
      password: process.env[entry.passwordEnv],
      securityContext: { group: entry.group },
    };
  },
  contextToGroups: (context) => {
    const group = context?.securityContext?.group;
    return group ? [group] : [];
  },
};
```

Full version, failing closed when a password is unset: [`../examples/cube.js`](../examples/cube.js).

- Passwords come from the environment, never the repo.
- Refuse to start when a password is missing; never fall back to an open SQL API.
- The same error text for a wrong user and a wrong password.
- Check your Cube version's docs: Cube 1.x matches access policies on groups (`contextToGroups`); some releases match on roles (`contextToRoles`).

## Step 5: Restrict Rows When Needed

A view's policy can filter rows by the security context, for example a client user who should see only their company:

```yaml
    access_policy:
      - group: client_portal
        row_level:
          filters:
            - member: company_id
              operator: equals
              values: ["{ securityContext.company_id }"]
```

Row filters use the same format as REST API query filters (`equals`, `contains`, `gte`, …, combined with `and`/`or`). Newer Cube releases write the value as `"{ userAttributes.company_id }"`; check the [access policy reference](https://docs.cube.dev/reference/data-modeling/data-access-policies) for your version. A policy without `row_level` allows all rows.

## Step 6: Prove the Boundaries

For each SQL API user, prove both sides (`test-the-model.md`):

- it can query its own views;
- it's refused on every cube and on other groups' views;
- an agent's view returns no ID columns.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

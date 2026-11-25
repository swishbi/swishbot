# Publish a View and Decide Who Can Query It

Views are the only way consumers reach data. Each view covers one subject and is shared by every consumer group allowed to see that subject, through an access policy. Each consumer still logs in as its own SQL API user.

## Step 1: Decide the Views and Who Shares Them

**One view per subject**, named for the subject (`finance_profit_and_loss`, `finance_general_ledger`), not for a consumer. A view's name and its member names are the contract: dashboards, saved questions and agent prompts use them.

| Consumer | Login and group | Views |
|----------|-----------------|-------|
| BI tool (Metabase, Superset) | `metabase` | The subject views |
| The business's AI agent (Claude Code through an SQL MCP) | `agent` | The same subject views |
| A consumer that must not see everything (a client portal, an agent acting for someone outside the business) | its own | Restricted views only (Step 5) |

- **Share by default.** When the same people reach the data through both the BI tool and an agent (often the BI tool's own MCP already gives the agent the BI view), a second, narrower view keeps nothing from them. It only doubles the views, the access lists and the boundary tests, and the two copies drift apart.
- **Separate logins anyway.** One SQL API user per consumer, even when they share views, so either can be turned off alone and the logs tell them apart.
- **Restrict only for a reason.** Add a restricted view when a consumer must not see something. Design it around what that consumer mustn't see, and name it for the consumer (`client_profit_and_loss`).

## Step 2: Write the View

```yaml
views:
  - name: finance_profit_and_loss
    title: "Profit and loss"
    description: "Monthly P&L by account, for the BI tool and the business's AI agent."

    access_policy:
      - group: metabase
        row_level:
          allow_all: true
      - group: agent
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

The view exposes exactly the members its `includes` lists. Anything not listed doesn't exist for any consumer of that view.

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

## Step 5: Restrict a Consumer When Needed

Only for a consumer that must not see something (Step 1). Give it its own restricted view, which lists only the members it may see, and grant that view to its group alone. Never widen a shared view's audience to a consumer it wasn't designed for.

A view's policy can also filter rows by the security context, for example a client user who should see only their company:

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

- it can query every view granted to its group;
- it's refused on every cube and on every view not granted to its group;
- a shared view returns the same total to every group;
- a restricted view lists none of the members its consumer mustn't see.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*

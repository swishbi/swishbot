// Copyright (c) 2026 Swish BI Limited. All rights reserved.
//
// Cube Core configuration: SQL API users mapped to access-policy groups.
//
// - Only the users listed here can log in to the SQL API (Postgres
//   protocol). Each consumer has its own login and group, even when the
//   groups are granted the same views.
// - Passwords come from the environment, never from the repo. Cube refuses
//   to start when one is missing, instead of running an open SQL API.
// - contextToGroups hands each user's group to the access policies in the
//   model; views grant groups, cubes grant nobody.
'use strict';

const SQL_USERS = {
  metabase: { passwordEnv: 'CUBE_SQL_PASSWORD_METABASE', group: 'metabase' },
  agent: { passwordEnv: 'CUBE_SQL_PASSWORD_AGENT', group: 'agent' },
};

for (const [user, entry] of Object.entries(SQL_USERS)) {
  if (!process.env[entry.passwordEnv]) {
    throw new Error(`${entry.passwordEnv} is not set; refusing to start Cube with an open SQL API (user "${user}")`);
  }
}

module.exports = {
  checkSqlAuth: (request, user) => {
    const entry = SQL_USERS[user];
    if (!entry) {
      // The same message for a wrong user and a wrong password.
      throw new Error(`Incorrect user name "${user}" or password`);
    }
    return {
      password: process.env[entry.passwordEnv],
      securityContext: { group: entry.group },
    };
  },

  contextToGroups: (context) => {
    const securityContext = context && context.securityContext ? context.securityContext : context;
    const group = securityContext && securityContext.group;
    return group ? [group] : [];
  },
};

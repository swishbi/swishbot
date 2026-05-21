#!/usr/bin/env bash
# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Hook script: Reject dangerous SQL operations in Bash commands.
# Invoked by the dba-security skill's PreToolUse hook on Bash tool calls.
#
# Reads the tool input from stdin (JSON with "tool_input.command" and "cwd").
# Scoped: only fires when CWD or an ancestor (up to 8 levels) contains either
# a dbt_project.yml file or a .swishbot-enforce opt-in marker. Anywhere else
# the hook is a no-op so it does not interfere with unrelated work.
#
# Exits 2 + prints a message to block the operation.
# Exits 0 to allow it.

set -euo pipefail

INPUT=$(cat)

COMMAND=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', '') or data.get('command', ''))
except Exception:
    pass
" 2>/dev/null || true)

CWD=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('cwd', ''))
except Exception:
    pass
" 2>/dev/null || true)

[ -z "$COMMAND" ] && exit 0
[ -z "$CWD" ] && CWD="$PWD"

in_scope() {
    local dir="$1"
    local depth=0
    while [ -n "$dir" ] && [ "$dir" != "/" ] && [ "$depth" -lt 8 ]; do
        if [ -f "$dir/dbt_project.yml" ] || [ -f "$dir/.swishbot-enforce" ]; then
            return 0
        fi
        dir=$(dirname "$dir")
        depth=$((depth + 1))
    done
    return 1
}

if ! in_scope "$CWD"; then
    exit 0
fi

UPPER=$(printf '%s' "$COMMAND" | tr '[:lower:]' '[:upper:]')

DANGEROUS_PATTERNS=(
    "DROP DATABASE"
    "DROP SCHEMA"
    "DROP TABLE"
    "DROP VIEW"
    "TRUNCATE"
    "DELETE FROM.*WITHOUT"
    "GRANT ALL"
    "REVOKE ALL"
)

for PATTERN in "${DANGEROUS_PATTERNS[@]}"; do
    if printf '%s' "$UPPER" | grep -qE "$PATTERN"; then
        echo "BLOCKED: Detected dangerous SQL operation matching '$PATTERN'."
        echo "The dba-security skill blocks destructive DDL by default."
        echo "If this is intentional, ask the user to confirm before proceeding."
        exit 2
    fi
done

exit 0

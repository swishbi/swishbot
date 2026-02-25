#!/usr/bin/env bash
# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Hook script: Reject dangerous SQL operations in Bash commands.
# Invoked by the dba-security skill's PreToolUse hook on Bash tool calls.
#
# Reads the tool input from stdin (JSON with "command" field).
# Exits 2 + prints a message to block the operation.
# Exits 0 to allow it.

set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('command', ''))
except Exception:
    pass
" 2>/dev/null || true)

if [ -z "$COMMAND" ]; then
    exit 0
fi

# Normalize to uppercase for matching
UPPER=$(echo "$COMMAND" | tr '[:lower:]' '[:upper:]')

# Block destructive DDL without explicit confirmation
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
    if echo "$UPPER" | grep -qE "$PATTERN"; then
        echo "BLOCKED: Detected dangerous SQL operation matching '$PATTERN'."
        echo "The dba-security skill blocks destructive DDL by default."
        echo "If this is intentional, ask the user to confirm before proceeding."
        exit 2
    fi
done

exit 0

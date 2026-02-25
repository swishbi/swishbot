#!/usr/bin/env bash
# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Hook script: Reject dangerous Terraform operations in Bash commands.
# Invoked by the iac-terraform skill's PreToolUse hook on Bash tool calls.
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

# Block destructive Terraform operations without explicit confirmation
DANGEROUS_PATTERNS=(
    "TERRAFORM DESTROY"
    "TERRAFORM FORCE-UNLOCK"
    "TERRAFORM APPLY.*-AUTO-APPROVE.*DESTROY"
    "TERRAFORM STATE RM"
    "TERRAFORM STATE MV"
    "TERRAFORM IMPORT"
)

for PATTERN in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$UPPER" | grep -qE "$PATTERN"; then
        echo "BLOCKED: Detected dangerous Terraform operation matching '$PATTERN'."
        echo "The iac-terraform skill blocks destructive operations by default."
        echo "If this is intentional, ask the user to confirm before proceeding."
        exit 2
    fi
done

exit 0

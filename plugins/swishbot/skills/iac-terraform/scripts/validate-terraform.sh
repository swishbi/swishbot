#!/usr/bin/env bash
# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Hook script: Reject dangerous Terraform operations in Bash commands.
# Invoked by the iac-terraform skill's PreToolUse hook on Bash tool calls.
#
# Reads the tool input from stdin (JSON with "tool_input.command" and "cwd").
# Scoped: only fires when CWD or an ancestor (up to 8 levels) contains any
# *.tf file, a .terraform/ directory, or a .swishbot-enforce opt-in marker.
# Anywhere else the hook is a no-op.
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
        if [ -f "$dir/.swishbot-enforce" ] || [ -d "$dir/.terraform" ]; then
            return 0
        fi
        for f in "$dir"/*.tf; do
            [ -f "$f" ] && return 0
            break
        done
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
    "TERRAFORM DESTROY"
    "TERRAFORM FORCE-UNLOCK"
    "TERRAFORM APPLY.*-AUTO-APPROVE.*DESTROY"
    "TERRAFORM STATE RM"
    "TERRAFORM STATE MV"
    "TERRAFORM IMPORT"
)

for PATTERN in "${DANGEROUS_PATTERNS[@]}"; do
    if printf '%s' "$UPPER" | grep -qE "$PATTERN"; then
        echo "BLOCKED: Detected dangerous Terraform operation matching '$PATTERN'."
        echo "The iac-terraform skill blocks destructive operations by default."
        echo "If this is intentional, ask the user to confirm before proceeding."
        exit 2
    fi
done

exit 0

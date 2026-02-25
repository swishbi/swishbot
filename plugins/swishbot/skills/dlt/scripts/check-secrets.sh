#!/usr/bin/env bash
# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Hook script: Warn if credentials appear in pipeline code.
# Scans file content for common secret patterns before writing.
#
# Reads tool input from stdin (JSON with "content" and "file_path" fields).
# Exits 2 to block if secrets are detected. Exits 0 otherwise.

set -euo pipefail

INPUT=$(cat)

# Extract content to check — look in both content and new_string fields
CONTENT=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('content', data.get('new_string', '')))
except Exception:
    pass
" 2>/dev/null || true)

if [ -z "$CONTENT" ]; then
    exit 0
fi

# Patterns that suggest hardcoded credentials
PATTERNS=(
    'password\s*=\s*["\x27][^"\x27]+'
    'api_key\s*=\s*["\x27][^"\x27]+'
    'secret\s*=\s*["\x27][^"\x27]+'
    'token\s*=\s*["\x27][A-Za-z0-9]+'
    'AKIA[0-9A-Z]{16}'
    'sk-[a-zA-Z0-9]{20,}'
    'ghp_[a-zA-Z0-9]{36}'
)

FOUND=0
for PATTERN in "${PATTERNS[@]}"; do
    if echo "$CONTENT" | grep -qiE "$PATTERN"; then
        if [ "$FOUND" -eq 0 ]; then
            echo "BLOCKED: Possible hardcoded credentials detected in pipeline code."
            echo ""
            FOUND=1
        fi
        echo "  - Pattern matched: $PATTERN"
    fi
done

if [ "$FOUND" -eq 1 ]; then
    echo ""
    echo "Use environment variables or a secrets manager instead of hardcoded values."
    echo "Example: os.environ['API_KEY'] or dlt.secrets.value"
    exit 2
fi

exit 0

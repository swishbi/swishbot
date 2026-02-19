#!/usr/bin/env bash
# Copyright (c) 2026 Swish BI Limited. All rights reserved.
#
# Hook script: Verify source YAML exists for staged models.
# Checks that when a staging model file is written, a corresponding
# _sources.yml file exists in the same directory.
#
# Reads tool input from stdin (JSON with "file_path" field).
# Exits 0 always (advisory only — prints warnings but does not block).

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | grep -oP '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"$//' || true)

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Only check staging model files (stg_*.sql)
BASENAME=$(basename "$FILE_PATH")
if [[ ! "$BASENAME" =~ ^stg_.*\.sql$ ]]; then
    exit 0
fi

# Look for a _sources.yml or _sources.yaml in the same directory
DIR=$(dirname "$FILE_PATH")
if ! ls "$DIR"/*_sources.yml "$DIR"/*_sources.yaml 2>/dev/null | head -1 > /dev/null 2>&1; then
    echo "WARNING: No _sources.yml found in $DIR"
    echo "Staging models should have a corresponding source YAML file."
    echo "Run the dbt 'Create Staging Source' workflow to generate one."
fi

exit 0

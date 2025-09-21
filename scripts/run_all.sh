#!/usr/bin/env bash
set -euo pipefail

FAILED=0

# Detect CI (non-interactive) environments so prompts are not used there
CI_DETECTED=0
if [ "${CI:-}" = "true" ] || [ "${GITHUB_ACTIONS:-}" = "true" ] || [ "${CI:-}" != "" ]; then
  CI_DETECTED=1
fi

echo "=== running tests ==="
python -m pytest -q || FAILED=1


if [ "$FAILED" -ne 0 ]; then
  echo "One or more checks failed"
  exit 1
fi

echo "All checks passed"
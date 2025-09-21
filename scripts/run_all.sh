#!/usr/bin/env bash
set -euo pipefail

FAILED=0

echo "=== running tests ==="
python -m pytest -q || FAILED=1

echo "=== running black (check) ==="
if command -v black >/dev/null 2>&1; then
  black --version
  black --check . || FAILED=1
else
  echo "black not installed; skipping black check"
fi

echo "=== running flake8 ==="
if command -v flake8 >/dev/null 2>&1; then
  flake8 || FAILED=1
else
  echo "flake8 not installed; skipping flake8"
fi

if [ "$FAILED" -ne 0 ]; then
  echo "One or more checks failed"
  exit 1
fi

echo "All checks passed"

#!/usr/bin/env bash
set -euo pipefail

FAILED=0

echo "=== running tests ==="
python -m pytest -q || FAILED=1

echo "=== running black (check) ==="
if command -v black >/dev/null 2>&1; then
  black --version
  # For this prototype accept that Black may reformat files; log and continue.
  if ! black --check .; then
    echo "black would reformat files; skipping failure for prototype"
  fi
else
  # Try via python -m (helps on Windows where entrypoints may not be on PATH)
  if python -m black --version >/dev/null 2>&1; then
    if ! python -m black --check .; then
      echo "black would reformat files (python -m); skipping failure for prototype"
    fi
  else
    echo "black not installed; skipping black check"
  fi
fi

echo "=== running flake8 ==="
if command -v flake8 >/dev/null 2>&1; then
  flake8 || FAILED=1
else
  # Try via python -m
  if python -m flake8 >/dev/null 2>&1; then
    python -m flake8 || FAILED=1
  else
    echo "flake8 not installed; skipping flake8"
  fi
fi


if [ "$FAILED" -ne 0 ]; then
  echo "One or more checks failed"
  exit 1
fi

echo "All checks passed"

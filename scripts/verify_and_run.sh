#!/usr/bin/env bash
# Installs dev dependencies (locally, user site) and runs the unified script.
set -euo pipefail

echo "Installing dev dependencies (may use cached packages)..."
python -m pip install -r requirements-dev.txt

echo "Running unified script..."
bash scripts/run_all.sh

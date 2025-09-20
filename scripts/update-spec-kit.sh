#!/usr/bin/env bash
set -euo pipefail

# updates local project with the latest spec-kit via uvx
# Usage: ./scripts/update-spec-kit.sh [--yes]
# If --yes is provided, automatically install uvx without prompting.

AUTO_YES=false
if [ "${1:-}" = "--yes" ]; then
  AUTO_YES=true
fi

require_uvx() {
  if command -v uvx >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

install_uvx_via_pipx() {
  echo "Installing pipx (user) and uvx via pipx..."
  python -m pip install --user pipx
  python -m pipx ensurepath
  echo "Installing uvx via pipx..."
  python -m pipx install uvx
  echo "uvx installed"
}

if require_uvx; then
  echo "uvx found. Proceeding to update spec-kit templates..."
else
  echo "uvx is not installed." >&2
  if [ "$AUTO_YES" = true ]; then
    install_uvx_via_pipx
  else
    read -rp "Install uvx via pipx for you? [y/N]: " REPLY
    case "$REPLY" in
      [Yy]*) install_uvx_via_pipx ;; 
      *) echo "uvx required to update spec-kit. Aborting."; exit 1 ;;
    esac
  fi
fi

# Run the update (fetch latest from Git and initialize current dir using shell scripts)
uvx --from git+https://github.com/github/spec-kit.git specify init --here --script sh

echo "spec-kit update complete."

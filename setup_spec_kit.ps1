# setup_spec_kit.ps1
# Ensure Python, virtual environment, and install/update spec-kit from GitHub

# Check for Python installation
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python is not installed. Please install Python 3.12+ from https://www.python.org/downloads/ and re-run this script."
    exit 1
}

# Create virtual environment if missing
if (!(Test-Path ".venv")) {
    python -m venv .venv
}

# Activate virtual environment
. .venv/Scripts/Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install or upgrade spec-kit from GitHub
pip install --upgrade git+https://github.com/github/spec-kit.git

Write-Host "spec-kit setup complete."

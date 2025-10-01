
# setup_spec_kit.ps1
# Robust setup for Python, venv, and spec-kit

# Check for Python installation
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "ERROR: Python is not installed. Please install Python 3.12+ from https://www.python.org/downloads/ and re-run this script."
    exit 1
}

# Create or repair virtual environment if missing or broken
if (!(Test-Path ".venv/Scripts/Activate.ps1")) {
    Write-Host "Creating or repairing virtual environment..."
    Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
    python -m venv .venv
}

# Activate virtual environment
if (Test-Path ".venv/Scripts/Activate.ps1") {
    . .venv/Scripts/Activate.ps1
    Write-Host "Virtual environment activated."
} else {
    Write-Host "ERROR: Could not activate virtual environment. Check Python installation and permissions."
    exit 1
}

# Upgrade pip
python -m pip install --upgrade pip

# Install or upgrade spec-kit from GitHub
try {
    pip install --upgrade git+https://github.com/github/spec-kit.git
    Write-Host "spec-kit setup complete."
} catch {
    Write-Host "ERROR: Failed to install spec-kit. Check your internet connection and permissions."
    exit 1
}

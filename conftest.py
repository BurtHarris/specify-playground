"""
pytest configuration and fixtures for Video Duplicate Scanner CLI tests.

This file sets up the test environment, including path configuration
to allow importing from the src/ directory.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
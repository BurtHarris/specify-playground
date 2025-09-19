"""
Entry point for the video duplicate scanner CLI.

This module provides the main entry point for the CLI application,
enabling execution via 'python -m src' or 'python src'.
"""

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add the parent directory to sys.path to enable relative imports
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from src.cli.main import main
    main()
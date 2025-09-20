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
    
    # If invoked as: python -m src <path> (no subcommand), many tests and
    # users expect that to behave like: python -m src scan <path>. Some test
    # runners invoke the module as a subprocess; in that case we may not be
    # able to reliably detect existing paths across different working dirs.
    # Use a conservative heuristic: if the last argument is a non-option
    # token (doesn't start with '-') and the first non-option isn't a
    # known subcommand, insert 'scan' before the last token so Click will
    # dispatch to the scan command. This covers common invocations like:
    #   python -m src <dir>
    #   python -m src --export OUT <dir>
    try:
        if len(sys.argv) >= 2:
            known_subcommands = {'scan', 'config', 'help', '--help', '-h'}

            # If none of the known subcommands are present in the provided
            # arguments and the last token is a non-option (likely a path),
            # insert 'scan' immediately after the script/module name so that
            # Click dispatches correctly. This handles invocations like:
            #   python -m src <dir>
            #   python -m src --export OUT <dir>
            argv_tail = sys.argv[1:]
            # If any known subcommand already present, do nothing
            if not any(token in known_subcommands for token in argv_tail):
                last_token = sys.argv[-1]
                if not last_token.startswith('-'):
                    # Insert 'scan' at position 1 (after script path)
                    # so that options remain in order after the subcommand.
                    sys.argv.insert(1, 'scan')
                    # Normalize argv[0] so Click's prog_name and help output
                    # display the module name 'src' when invoked via -m.
                    try:
                        sys.argv[0] = 'src'
                    except Exception:
                        pass
    except Exception:
        # Best-effort: if anything goes wrong here, fall back to normal
        # behavior and let Click handle the arguments. Avoid crashing at import.
        pass

    from src.cli.main import main
    main()
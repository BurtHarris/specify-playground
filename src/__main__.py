"""
Minimal CLI entrypoint for Video Duplicate Scanner.

This entrypoint supports implicit invocation patterns used by some
integration tests and shell users: when the module is invoked as
`python -m src [OPTIONS] <DIRECTORY>` and the DIRECTORY token is an
existing directory path, insert the explicit 'scan' subcommand so Click
dispatches correctly. This insertion is conservative and only happens
when an actual existing directory is found among the positional args.

This module enforces the runtime Python version requirement (3.12+)
so early failures are clear when the CLI is executed in older runtimes.
"""

import sys
import os
from pathlib import Path

from src.cli.main import main


# Enforce Python runtime version requirement early (T001)
if sys.version_info < (3, 12):
    sys.stderr.write(
        "specify-playground: Python 3.12 or newer is required. "
        f"Current version: {sys.version.split()[0]}\n"
    )
    sys.exit(2)


def _maybe_insert_scan_subcommand():
    # Only examine user-provided args (skip program name)
    if len(sys.argv) <= 1:
        return

    # Don't modify if a recognized subcommand is already present
    # (e.g., 'scan' or 'config').
    recognized = set(getattr(main, "commands", {}).keys())

    # Search for the first token that looks like an existing directory and
    # is not an option (doesn't start with '-') and not a recognized command.
    for i, token in enumerate(sys.argv[1:], start=1):
        if token.startswith("-"):
            continue
        if token in recognized:
            # Found an explicit subcommand; nothing to do.
            return
        try:
            p = Path(token)
            if p.exists() and p.is_dir():
                # Move scan-related options (that may appear before the
                # directory) to immediately after the inserted 'scan'
                # token so the subcommand will parse them. This handles
                # invocations like: python -m src --recursive --export out.yaml <dir>
                scan_options_with_value = {"--export", "--threshold"}

                # Collect indices of tokens between program name and dir
                pre_indices = list(range(1, i))
                move_indices = []
                j = 1
                while j < i:
                    tok = sys.argv[j]
                    if tok in scan_options_with_value:
                        # move option and its value (if present)
                        move_indices.append(j)
                        if j + 1 < i:
                            move_indices.append(j + 1)
                        j += 2
                    elif tok.startswith("-"):
                        move_indices.append(j)
                        j += 1
                    else:
                        j += 1

                # Build moved tokens in original order
                moved = [sys.argv[idx] for idx in sorted(move_indices)]

                # Build remaining tokens (excluding moved ones)
                remaining = [
                    sys.argv[k]
                    for k in range(len(sys.argv))
                    if k not in move_indices
                ]

                # Find new index of the directory token in remaining
                # (it shifts left by count of removed tokens before it)
                # Insert 'scan' before the directory and then the moved options
                # after 'scan'.
                # Locate dir in remaining (first non-option, non-command token)
                r_dir_index = None
                for ri, rt in enumerate(remaining[1:], start=1):
                    if not rt.startswith("-") and rt not in recognized:
                        r_dir_index = ri
                        break

                if r_dir_index is None:
                    # Fallback: just insert scan at original i
                    insert_at = i
                    remaining = sys.argv[:]
                    moved = []
                    new_argv = (
                        remaining[:insert_at]
                        + ["scan"]
                        + moved
                        + remaining[insert_at:]
                    )
                else:
                    new_argv = (
                        [remaining[0]]
                        + remaining[1:r_dir_index]
                        + ["scan"]
                        + moved
                        + remaining[r_dir_index:]
                    )

                sys.argv[:] = new_argv

                if os.environ.get("SPECIFY_DEBUG_ARGV") == "1":
                    print(
                        f"[__main__] relocated options and inserted 'scan'; argv={sys.argv}"
                    )
                return
        except Exception:
            continue


if __name__ == "__main__":
    # Optionally print argv before/after insertion for debugging
    if os.environ.get("SPECIFY_DEBUG_ARGV") == "1":
        print(f"[__main__] before insertion argv={sys.argv}")
    _maybe_insert_scan_subcommand()
    if os.environ.get("SPECIFY_DEBUG_ARGV") == "1":
        print(f"[__main__] after insertion argv={sys.argv}")
    main()

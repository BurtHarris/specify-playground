AI run guidance

The repository requires that all test and quality checks are executed in a terminal by the assistant before making changes that affect behavior.

Please follow these steps before editing or committing code:

1. Run the unified script which executes tests and linters:

   bash scripts/run_all.sh

2. If the script fails, fix the reported issues locally and re-run until green.

3. Commit changes only after checks pass. CI will run the same script on push/PR.

This file is a guidance contract for automation and reviewers; repository files cannot technically force the assistant to use a specific tool, but following this convention ensures reproducible runs.

Quick helper scripts
--------------------

Two convenience scripts are provided under `scripts/` to accelerate common maintenance flows:

- `scripts/apply_quick_fixes.sh` - applies small, safe automated edits that reduce noisy linter failures (f-string without placeholders, `assert False` contract placeholders, and simple `== True/False` assertions in tests). Review changes before committing.
- `scripts/verify_and_run.sh` - installs dev dependencies from `requirements-dev.txt` and runs the unified script `scripts/run_all.sh` (useful for local CI reproduction).

Usage examples (run in a bash-capable terminal):

```bash
# Apply quick, safe fixes (review diffs afterwards)
bash scripts/apply_quick_fixes.sh

# Run full verification (installs dev deps if needed)
bash scripts/verify_and_run.sh
```

Notes
-----
- These helper scripts are intentionally conservative; they should be reviewed and adapted when making broader behavioral changes.
- The repository's canonical check remains `bash scripts/run_all.sh` which CI runs on push/PR.

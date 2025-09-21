AI run guidance

The repository requires that all test and quality checks are executed in a terminal by the assistant before making changes that affect behavior.

Please follow these steps before editing or committing code:

1. Run the unified script which executes tests and linters:

   bash scripts/run_all.sh

2. If the script fails, fix the reported issues locally and re-run until green.

3. Commit changes only after checks pass. CI will run the same script on push/PR.

This file is a guidance contract for automation and reviewers; repository files cannot technically force the assistant to use a specific tool, but following this convention ensures reproducible runs.

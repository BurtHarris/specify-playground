# Recurring test cancellation when running pytest in the integrated workspace terminal

Status
------
- Screenshot attached: `BUG_REPORTS/screenshot.png`.
- Remote issue: https://github.com/BurtHarris/specify-playground/issues/10

Summary
-------
Intermittent cancellations observed when running pytest (and other commands) in the editor integrated terminal. Failures appear as immediate UI cancel, `SystemExit(2)` emitted by Click-based CLI code, or `bash: pytest: command not found` when the venv is not activated.

Environment
-----------
- OS: Windows
- Shell: `bash.exe` (Git Bash / WSL-like)
- Repository: `specify-playground` (branch: any)
- Python: project targets 3.12+; project venv expected at `.venv`

Minimal reproduction
-------------------
1) Activate project venv in integrated terminal:
   source .venv/Scripts/activate
2) Run the failing integration test:
   pytest -q tests/integration/test_progress_reporting.py::TestProgressReportingIntegration::test_progress_reporting_during_cli_scan
3) Observe cancellation, immediate `SystemExit(2)`, or missing `pytest` if venv not activated.

Observed failure modes
----------------------
- Immediate UI cancellation of the integrated terminal run.
- CLI triggers `ctx.exit(2)` causing `SystemExit(2)` in tests.
- `pytest` missing from PATH when the venv is not active in the integrated terminal.

Quick checks
------------
- After activation, run `which pytest` or `pytest --version` to confirm venv is active.
- Reproduce the same command in an external terminal to rule out editor-specific behavior.
- If CLI emits `SystemExit(2)`, inspect `src/cli/main.py` for `ctx.exit`/`sys.exit` usages or implicit top-level dispatch behavior.

Diagnostics requested
---------------------
- Integrated terminal output saved to a file (use `tee`).
- Shell trace with `bash -x` saved to `pytest_trace.log`:
  bash -x -c "pytest -q tests/integration/test_progress_reporting.py::TestProgressReportingIntegration::test_progress_reporting_during_cli_scan" 2>&1 | tee pytest_trace.log
- VS Code version, integrated terminal path (bash.exe), and active extension list.

Attachments
-----------
- `BUG_REPORTS/screenshot.png` (attached)

Next steps
----------
1) Reproduce the command in an external terminal with the venv activated; if it succeeds, the issue is likely editor-specific.
2) If `SystemExit(2)` is reproducible, update tests to call the `scan` subcommand explicitly or restore implicit dispatch in `src/cli/main.py`.
3) Attach `pytest_trace.log` and editor debug logs to the GitHub issue for triage.

Assignee: BurtHarris


PR: Add Typer CLI adapter, robust DB persistence/recovery, and test compatibility shim

Summary:
- Introduces a Typer-based CLI adapter while preserving the existing Click implementation.
- Adds robust SQLite file-hash persistence with semantics: create DB when missing (INFO), detect and regenerate corrupted DB with a `.corrupt` backup (WARNING), and fall back to an in-memory DB on unrecoverable errors.
- Centralizes logger wiring to the DI container (prefers RichHandler when available and ensures stdout capture), replaces `--log-level` with `--verbose/--debug/--warning` semantics, and ensures library code returns numeric exit codes (adapters convert to SystemExit).
- Adds a test compatibility shim so existing tests run against the Typer adapter and new unit tests covering DB recovery; updates entrypoints to prefer the Typer adapter.

Tests:
- Full test suite passed locally (all tests green). See CI for platform-specific checks.

Notes for reviewers:
- Review DB recovery logic in `src/services/file_database.py` (sanity query, backup behavior, fallback to in-memory DB).
- Confirm logger wiring in `src/lib/container.py` and CLI flag semantics in `src/cli/*`.
- Ensure the Typer adapter behaviour in `src/cli/typer_cli.py` matches expectations for programmatic invocation (returns exit codes) and that Click compatibility remains.

Suggested reviewers: @maintainer-a, @maintainer-b

Merging:
- Recommend squash-and-merge; include the one-line changelog entry from `CHANGES.md`.

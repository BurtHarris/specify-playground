Title: Restore focused unit tests for `src/services/file_scanner.py` and simplify FileScanner

Summary
-------
The `FileScanner` implementation in `src/services/file_scanner.py` contains extensive logic to support unit tests that use `Mock(spec=Path)` and other test doubles (mock-specific branches, `_mock_name` checks, skipping resolution, verbose debug prints). This complexity makes the code harder to maintain and encourages brittle unit tests that depend on internal scanner behavior. The project needs an issue to restore a clear testing strategy: reintroduce focused unit tests for `validate_file` and other edge cases while simplifying `FileScanner` to rely on real filesystem semantics.

Motivation
----------
- Current code mixes production logic with many test-specific workarounds.
- Mock-specific branches add complexity and increase maintenance cost.
- Integration tests are valuable but cannot reliably or quickly test certain corner cases (permission errors, stat/os.access failures, Path resolution behavior).
- Restoring unit tests will make regressions easier to detect, while simplifying `FileScanner` will reduce technical debt.

Proposed change
---------------
1. Simplify `src/services/file_scanner.py`:
   - Remove `_mock_name` checks and other mock-specific branches.
   - Remove unconditional `DEBUG_VALIDATE` prints or gate them behind an env flag.
   - Use straightforward `pathlib.Path` operations: `resolve()`, `exists()`, `is_file()`, `os.access`, and `stat()` with clear exception handling.
2. Restore focused unit tests (in `tests/unit/`):
   - Unit tests covering `validate_file` behaviors: extension filtering, non-existent files, unreadable files, zero-size files, and stat failures (mock `stat()` raising).
   - Unit tests for directory scanning edge cases: permission denied when listing, fallback to glob, deterministic ordering.
3. Keep integration tests for end-to-end scanning behavior and cross-component interactions.

Acceptance criteria
-------------------
- A new issue file exists describing the change and outlining acceptance criteria (this file).
- `src/services/file_scanner.py` is simplified to remove test-specific branches.
- Unit tests for `validate_file` are restored and pass locally in CI.
- Integration tests remain in place and continue to pass.

Notes
-----
This issue is intended to start a discussion and coordinate work. Do not remove unit tests before the team agrees on the new approach and CI validation is in place.

Postpone cloud-status
---------------------
As an interim measure, the `--cloud-status` CLI option will be temporarily removed from the user-facing CLI until cloud-status behavior and tests are stabilized. A follow-up issue should be created to reintroduce cloud-status filtering with clear unit and integration tests that validate cloud detection, persistence, and CLI behavior.

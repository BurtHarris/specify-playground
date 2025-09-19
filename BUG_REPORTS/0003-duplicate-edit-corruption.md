Title: Duplicate/overlapping programmatic edits produce malformed Python files (example: src/services/file_scanner.py)

Summary (high priority: Python indentation/parse errors):
Programmatic edits are producing duplicated or overlapping Python code blocks which result in Python parse errors — frequently IndentationError — at import/compile time. The most visible symptom is an unexpected IndentationError when running `python -m py_compile` or during pytest collection. This is a class-level issue (affecting programmatic patch/replace workflows), not limited to a single file. Example affected file: `src/services/file_scanner.py` on branch `004-generalize-file-support`.

Severity: P1 (blocks CI/test collection)

Reproduction (example):
1. On branch `004-generalize-file-support`, open `src/services/file_scanner.py`.
2. Run a syntax check:
   python -m py_compile "e:\\specify-playground\\src\\services\\file_scanner.py"
3. Observe an IndentationError (unexpected indent) reported; opening the file shows duplicated top-level blocks and repeated class/function definitions.

Observed symptoms:
- Multiple shebang/module docstrings repeated.
- More than one `class FileScanner` definition or nested fragments in the same file.
- Helper functions duplicated with conflicting indentation.
- IndentationError during python compile or pytest collection.
- Literal tab character scan may show no tabs; the root cause is duplicated/malformed content.

Probable root causes:
- Non-atomic patch application: apply_patch or similar tool applied partial diffs that overlap with older content instead of replacing the file wholesale.
- Incomplete context matching in the patch generator causing appended fragments rather than replaced regions.
- Human-created overlapping patches: multiple edits with similar contexts applied sequentially without first removing previous content.

Immediate mitigation recommendations:
1. Atomic file replacement: For large refactors, perform a delete + create (single replacement) rather than multiple incremental edits.
2. Compile guard: Add `python -m py_compile` checks as a gating step before commit/CI acceptance.
3. Patch verification: After programmatic edits, run a verification step that ensures the modified file contains only one top-level class definition where expected and no duplicated docstring/shebang.
4. Preserve backups: When automated edits are applied, create a backup copy (`.bak`) to allow quick diff and revert.

Longer-term fixes:
- Harden the patching tool to detect overlapping contexts and fail the patch rather than producing partial merges.
- Add an automated smoke test in CI that attempts to import each changed module (or run `python -m py_compile` across the repo) and fails fast.
- Improve developer guidance: for large refactors, prefer single-file replacement PRs with human review.

Artifacts to attach:
- Snapshot of the malformed file (`src/services/file_scanner.py`).
- Output of `python -m py_compile` showing IndentationError.
- Sequence of applied patches or the patch source if available.

Branch/tag recommendations:
- Repro branch: `004-generalize-file-support` (current)
- Suggested tag for triage: `bug/duplicate-edit-corruption-004-generalize-file-support`

Owner and triage:
- Assign to the team that owns programmatic patch tooling and the file refactor author.

Next steps I can take:
- Create the suggested git tag locally and attempt to push it to origin (note: push may fail if remote credentials or network not available).
- Produce a PR with an atomic overwrite of the broken file and run `python -m py_compile` as part of the PR checks.

Contact:
- Provide the developer who ran these changes for follow-up and context (session logs available in workspace).

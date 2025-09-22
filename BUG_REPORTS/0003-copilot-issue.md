Title: Copilot-assisted programmatic edits can produce duplicated Python code → IndentationError (repro tag included)

Repository: https://github.com/BurtHarris/specify-playground
Repro tag: bug/duplicate-edit-corruption-004-generalize-file-support (commit f6b0539)

Summary
Automated programmatic edits (Copilot-assisted patch generation + apply step) have produced duplicated or overlapping Python code blocks that cause Python parse errors at import time (IndentationError). The issue appears to be in the patch application stage (context matching/atomic write) for Copilot workflows that apply multiple edits iteratively.

Steps to reproduce
1. Clone the repository and check out the repro tag:
   git fetch origin tag bug/duplicate-edit-corruption-004-generalize-file-support
   git checkout tags/bug/duplicate-edit-corruption-004-generalize-file-support
2. Inspect the file: `src/services/file_scanner.py` — it contains duplicated code blocks produced by prior patch attempts.
3. Run a syntax-check:
   python -m py_compile "e:\\specify-playground\\src\\services\\file_scanner.py"
   Expect an IndentationError describing unexpected indent.

Attachments in repository
- BUG_REPORTS/0003-duplicate-edit-corruption.md — detailed diagnostics and suggested mitigations
- BUG_REPORTS/attachments/file_scanner_current.py — current copy of the malformed file for quick download

Configuration / environment notes
- VS Code: reproduced on both Stable and Insiders builds
- Extension: Copilot extension active during automated edits
- LLMs: observed with multiple LLM backends; issue reproduces across models
- OS: Windows, PowerShell (`pwsh.exe`) default shell
- Python: 3.12+ (project requirement), compile checks done with local python

Observed behavior
- The malformed file contains repeated shebang/docstring blocks, duplicated class and helper definitions, and nested/misaligned fragments that trigger IndentationError on parse.
- Manual execution of the same commands in the terminal works; the corruption appears when edits are applied programmatically using the patcher/apply flow.

Why this likely involves Copilot integration
- The workflow that generated the malformed file was Copilot-assisted patch generation followed by an automated apply step executed from the editor/extension environment; the interaction between patch generation and file writes is suspect.

Suggested triage actions for Copilot/extension team
- Investigate whether extension-driven file writes can be non-atomic or can interleave when multiple write operations are invoked.
- Recommend atomic write patterns (write-to-temp + rename) in extension SDKs and dev guidance.
- Add a post-edit syntax verification option in the extension: run a language-specific parse check and abort/revert on parse failure.
- Inspect the apply_patch implementation used by helper tooling to ensure it does not append fragments accidentally when context-matching fails.

Requested assistance
- Confirmation whether Copilot or the VS Code extension APIs could lead to such non-atomic or duplicated writes.
- Guidance on best practices for extensions or programmatic editors that apply multiple edits in sequence.

Contact / follow-up
- Repro tag: bug/duplicate-edit-corruption-004-generalize-file-support
- If helpful, the repo owner can provide additional logs or grant access to session logs collected during the repair attempts.

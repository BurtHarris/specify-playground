# Contributing — Spec Kit workflow (short)

This project uses Spec Kit for spec-driven development. Quick reference for contributors:

Project branch policy (current)
- For simplicity, accept the feature branch auto-created by `/specify`.
- Teams may adopt different branching policies later; add a short note here if you do.

Multi-feature workflow (short)
1. Run `/specify` for each idea you want to draft. Each run creates `specs/XXX-feature/spec.md` and a feature branch.
2. When ready to work on a feature, check out its branch.
3. Run `/plan` on the branch to generate `plan.md` and supporting artifacts.
4. Run `/tasks` on the branch to generate `tasks.md` (actionable tasks).
5. Implement and iterate on the branch; open PRs when ready.

Post-/specify checklist
- Review `specs/XXX-feature/spec.md` for correctness.
- Delete branches you don't want to keep.
- Commit and push artifacts you intend to keep with clear messages.

Notes
- This CONTRIBUTING file is intentionally minimal; refer to `SPECIFY_ASSUMPTIONS.md` for detailed assumptions, templates, and governance notes.

## OneDrive Integration Testing

OneDrive features require Windows testing due to platform-specific Windows API usage:

- **Windows Required**: OneDrive cloud status detection only works on Windows platforms
- **Test Coverage**: Include both Windows API tests and cross-platform compatibility tests
- **Mock Testing**: Use ctypes mocking for non-Windows CI/CD environments
- **Integration Tests**: Verify OneDrive detection with real files when possible
- **Error Handling**: Test graceful degradation on non-Windows platforms

Testing checklist for OneDrive features:

- [ ] Windows API detection tests pass on Windows
- [ ] Non-Windows platforms gracefully degrade to local file handling
- [ ] Mock tests cover Windows API error conditions
- [ ] Integration tests verify real file detection accuracy

## Development Notes: IoC and Series Detection

The project uses a lightweight IoC/container pattern for dependency injection to make components (logger, progress reporter, hasher, and database) swappable for testing and for embedding in other tools. When adding new services, prefer constructor injection or retrieving a container-provided collaborator instead of creating import-time singletons.

Series-detection is intentionally conservative and audit-only: files that look like numbered series (episodes, parts) are recorded as "series-like groups" in scan metadata but are not skipped from hashing or duplicate confirmation. This avoids false negatives while still providing reviewers with a clear, auditable signal about groups that may be sequential parts rather than true duplicates.

Key points for contributors:

- Use `Container()` to obtain a configured logger when writing new modules so the CLI `--debug`/`--warning` flags propagate to the component.
- Do not skip hashing solely based on series-like heuristics; hashing and size checks remain the source of truth for confirmed duplicates.
- When introducing heuristics, make them audit-only by default and record the rationale in scan metadata so reviewers can decide programmatically or manually.

Commit message template
-----------------------

Use a short, consistent commit message when adding or regenerating spec artifacts. Example:

<type>: <short description> [spec: XXX-feature]

Examples:
- feat: add initial spec for XXX-feature [spec: 001-xxx-feature]
- docs: regenerate plan & tasks after spec update [spec: 001-xxx-feature]

PR checklist (basic)
--------------------

- [ ] This PR targets the correct feature branch (e.g., `001-xxx-feature`).
- [ ] `specs/` files are present and updated as needed (spec.md, plan.md, tasks.md).
- [ ] Generated artifacts were reviewed locally and linted where applicable.
- [ ] Commit messages reference the spec ID in square brackets (e.g., `[spec: 001-xxx-feature]`).
- [ ] Add a brief description in the PR body summarizing the spec -> plan -> tasks flow for reviewers.

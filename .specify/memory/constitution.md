<!--
Sync Impact Report
- Version change: 2.1.1 -> 2.1.2
- Modified principles: placeholders filled with concrete principle titles and descriptions (no renames)
- Added sections: Operational Constraints, Development Workflow (concretized)
- Removed sections: none
- Templates requiring updates: /.specify/templates/plan-template.md ✅ updated
						 /.specify/templates/spec-template.md ✅ updated
						 /.specify/templates/tasks-template.md ✅ updated
						 /specs/* (plans referencing old version) ⚠ pending manual sync
- Follow-up TODOs: RATIFICATION_DATE intentionally deferred (TODO)
-->

# Video Duplicate Scanner Constitution

## Core Principles

### I. Library-First
Every feature MUST begin as a reusable library or module. Libraries MUST be self-contained, have a clear public contract, and include unit tests and documentation. Consumers (CLI, services, or other libraries) SHOULD depend on libraries rather than on ad-hoc scripts.

### II. CLI Interface
All user-facing functionality MUST be exposed via a well-documented CLI where applicable. CLI behavior MUST follow text I/O conventions: stdin/args → stdout for data and human output, and stderr for errors and diagnostics. Structured output formats (YAML, JSON) MUST be supported for machine consumption.

### III. Test-First (NON-NEGOTIABLE)
Tests MUST be authored before implementation for any new behavior: failing contract/integration tests first, then implementation to make tests pass (Red-Green-Refactor). Test coverage MUST include unit tests for libraries, contract tests for public APIs, and integration tests for cross-component behavior.

### IV. Integration Testing
Integration tests MUST validate interactions between components, contracts, and external dependencies. Integration tests MUST be included for new library contracts, breaking-interface changes, and any feature that spans multiple modules or external services.

### V. Observability, Versioning & Simplicity
Observability: Runtime artifacts MUST emit structured logs and include sufficient metadata to debug issues; metrics and progress reporting SHOULD be included for long-running operations.
Versioning: Semantic versioning (MAJOR.MINOR.PATCH) MUST be used for released artifacts; breaking changes MUST increment MAJOR, new capabilities that remain backward compatible increment MINOR, and clarifications/typo fixes increment PATCH.
Simplicity: Design decisions MUST favor simplicity; unnecessary complexity is prohibited. YAGNI (You Ain't Gonna Need It) principles SHOULD guide feature additions.

## Operational Constraints
The project defines a minimal operational standard to ensure consistency:
- Language/runtime: Python 3.12+ is REQUIRED for development and CI.
- Filesystem API: `pathlib.Path` MUST be used for file operations; cross-platform compatibility (Windows, macOS, Linux) is REQUIRED.
- CLI framework: Click is the standard CLI framework for command parsing.
- Hashing: Streaming hash computation MUST be used for large files to limit memory usage; a modern keyed hash (e.g., blake2b) is RECOMMENDED for performance with a clear migration path if algorithm changes are required.
- Database/cache: SQLite (WAL mode) is the authorized on-disk cache for local sessions; designs that require higher scale MUST document migration steps.
- Error handling: Scans MUST continue on individual file errors and record failures in structured metadata.

## Development Workflow
- All work MUST follow Test-Driven Development (see Principle III).
- Pull requests MUST include failing tests for new behavior and pass CI with linting and unit/integration tests.
- Code reviews: At least one approver is REQUIRED for non-trivial changes; for constitution or governance changes, two maintainers or a documented majority of approvers are REQUIRED.
- Quality gates: Builds MUST pass formatting, linting, and tests before merge; integration changes MUST include contract test updates.

## Governance
Amendments to this constitution REQUIRE a documented PR that explains the change, adds or updates tests/templates affected by the change, and provides a migration plan where applicable. Amendments MUST be reviewed and approved by at least two project maintainers (or a documented majority when the maintainer count is greater than two). Emergency fixes MAY be applied with at least one maintainer approval and must be followed by a retrospective PR that formalizes the change.

Versioning policy for the constitution:
- MAJOR: Reserved for backward-incompatible governance changes (principle removal or redefinition).
- MINOR: New principle or material expansion of guidance.
- PATCH: Clarifications, wording fixes, and placeholder resolution.

Compliance Review Expectations:
- Every `/plan` execution MUST run the Constitution Check section and record PASS/FAIL in the plan's Phase 0 output.
- Templates that reference constitution rules MUST be updated as part of any amendment PR.

**Version**: 2.1.2 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-20
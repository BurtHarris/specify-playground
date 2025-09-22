<!--
Sync Impact Report
- Version change: 2.1.2 -> 3.0.0
- Modified principles: Library-First (clarified), CLI policy changed to Typer-preferred
- Added sections: Prototype Policy, Minimal Operational Constraints (prototype-focused)
- Removed sections: strict Click mandate (replaced by Typer preference)
- Templates requiring updates: /.specify/templates/plan-template.md ⚠ pending
						 /.specify/templates/spec-template.md ⚠ pending
						 /.specify/templates/tasks-template.md ⚠ pending
						 /.specify/templates/commands/*.md ⚠ pending
- Follow-up TODOs: Update templates to reflect Typer preference; verify CI entrypoints; remove Click-mandates from docs if present
-->

# Video Duplicate Scanner Constitution

## Core Principles

### I. Library-First
Every feature MUST begin as a reusable library or module with a clear public contract and unit tests. The CLI, services, and any UI layer MUST call into these libraries — not the other way around. Implementations MUST be small, focused, and composable.

### II. Prototype & DRY (PRIMARY)
For this standalone prototype, DRY, simplicity, and forward momentum are REQUIRED. Work spent on backward compatibility or migration scaffolding for pre-v1 artifacts is counter-productive and MUST be avoided. Code SHOULD be minimal and idiomatic; duplication is only acceptable when it reduces complexity and improves clarity for the prototype timeframe.

Rationale: The project is a prototype without legacy constraints; prioritizing DRY and minimal, testable code accelerates iteration and reduces maintenance overhead.

### III. Unified CLI (Typer-preferred)
The project MUST expose a unified, easy-to-use CLI. For this prototype Typer is the PREFERRED CLI framework due to its concise decorators, type-hint-driven parsing, and ergonomic programmatic call patterns. Using Typer reduces boilerplate and keeps CLI code DRY.

Rationale: Typer reduces ceremony and helps keep CLI adapter code minimal for fast iteration. Exceptions to Typer are allowed only when a clear, documented technical need for Click-specific behaviour exists.

### IV. Test-First (NON-NEGOTIABLE)
Tests MUST be written before or alongside implementation. Contract and integration tests that define public behaviour are REQUIRED. Unit tests MUST accompany all library code. CI MUST run the full test matrix on every PR.

### V. Simplicity & Observability
Simplicity is a rule: prefer minimal APIs, clear data shapes, and explicit error handling. Observability requirements are minimal for prototype: logging (structured when convenient) and concise progress reporting MUST exist for long-running tasks. Keep observability lightweight and opt-in.

## Prototype Policy
- Avoid optimization until correctness and tests are in place.
- No compatibility layers for previous CLI frameworks unless strictly necessary.
- Dependencies SHOULD be minimal and well-justified.
- Rapid experiment branches are permitted; merge to main only when accompanied by tests and documentation for the change.

## Minimal Operational Constraints
- Language/runtime: Python 3.12+ REQUIRED.
- File API: `pathlib.Path` MUST be used for filesystem operations.
- Hashing: Use streaming hashing for large files; prefer blake2b or SHA-256; document algorithm choice in code comments.
- Persistence: For prototype, an in-memory or simple SQLite-backed cache is acceptable; clear migration plan REQUIRED if switching storage later.
- CLI: Typer PREFERRED; keep a lightweight adapter for programmatic use when tests need it.
- Error handling: Failures on individual files MUST be recorded and not abort full scans.

## Development Workflow
- Continue to follow Test-First discipline.
- Small, focused PRs are encouraged; each PR MUST include at least one relevant test and a short description of the change.
- Reviewers MUST prioritize simplicity and DRY implementations during reviews.

## Governance
Amendments to this constitution require a PR with tests and template updates where applicable. For prototype-only governance, a single maintainer MAY ratify minor clarifications, but MAJOR governance changes (principle removal or redefinition) MUST have explicit agreement from two maintainers.

**Version**: 3.0.0 | **Ratified**: 2025-09-21 | **Last Amended**: 2025-09-21
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

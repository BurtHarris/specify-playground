## Bug report: Specify methodology lacks clear branching strategy guidance

Summary
-------
The Specify methodology documentation does not clearly specify when to create feature branches during the planning process, leading to confusion about whether planning work should occur on `main` or on a dedicated feature branch. This resulted in an AI assistant creating planning artifacts (`plan.md`) directly on `main` branch instead of following the expected pattern of working on a feature-specific branch.

**Related Issue**: This issue may be related to [Issue #299 "Specify, Plan, and Task phases are too coupled"](https://github.com/github/spec-kit/issues/299) in the [github/spec-kit](https://github.com/github/spec-kit) repository, which discusses branching strategy in team environments.  While I'm working solo, I think that moving branch creation to /plan time might help a lot.

The ambiguity affects both human contributors and AI assistants implementing the Specify workflow, potentially leading to branch management inconsistencies and merge conflicts.

Note: most of this issue is copilot generated, minor tweaks by the human author

Environment snapshot
--------------------

System
  - OS: Windows (PowerShell default, GitHub shell for Windows)
  - Repository: [BurtHarris/specify-playground](https://github.com/BurtHarris/specify-playground)
  - Current branch: main
  - Specify version: Current (as of 2025-09-19)

Context
  - Working repository has existing spec branches (002-hash-comparison, 003-onedrive-compat-the)
  - spec.md already exists on main for spec 004-generalize-file-support
  - AI assistant was asked to implement the spec and proceeded with planning on main
  - Repository main branch is currently unprotected (no branch protection rules)

Problem description
-------------------

### Expected behavior
Based on observation of existing branches in the repository:
1. Create feature branch named after spec (e.g., `004-generalize-file-support`)
2. Perform all planning work (`plan.md`, `research.md`, design artifacts) on feature branch
3. Complete implementation on feature branch
4. Merge feature branch back to `main` when complete

### Actual behavior
1. ✅ spec.md created on main (appears correct)
2. ❌ plan.md created directly on main branch
3. ❌ Planning process started without branch creation
4. ❌ Plan header shows **Branch**: `main` instead of feature branch name

### Root cause
The Specify methodology documentation does not explicitly state:
- When to create the feature branch (before planning? during `/plan` command?)
- Whether planning artifacts belong on main or feature branch
- The branching strategy expectations for the workflow

Commands to reproduce
--------------------

1. Have a `spec.md` on main branch
2. User asks AI to "implement this spec" or "how do we do that"
3. AI assistant follows available Specify documentation
4. Results in planning work on main instead of feature branch

```bash
# Current state (incorrect)
$ git branch
* main
$ ls specs/004-generalize-file-support/
plan.md  spec.md  # plan.md created on main

# Expected state
$ git branch  
  004-generalize-file-support
* main
$ git checkout 004-generalize-file-support
$ ls specs/004-generalize-file-support/
plan.md  spec.md  # plan.md created on feature branch
```

Evidence files
--------------

- `specs/004-generalize-file-support/plan.md` (created on main, header shows wrong branch)
- Git branch history showing existing pattern:
  ```
  002-hash-comparison (spec branch exists)
  003-onedrive-compat-the (spec branch exists)  
  003-onedrive-compat-the-config-file (spec branch exists)
  ```

User impact
-----------

**High**: Process confusion affects:
- AI assistants implementing Specify workflow
- Human contributors following methodology  
- Repository maintainers expecting consistent branching
- Potential merge conflicts when multiple specs are worked on simultaneously

**Frequency**: Likely to occur on every new spec implementation until clarified

Suggested solutions (prioritized)
--------------------------------

### Option 1: Update methodology documentation (Low effort, high impact)
Add explicit branching guidance to Specify docs:
```markdown
## Branching Strategy
Before beginning Phase 0 planning:
1. Create feature branch: git checkout -b {spec-number}-{spec-name}
2. All planning artifacts (plan.md, research.md, etc.) go on feature branch
3. Implementation occurs on feature branch
4. Merge to main when complete
```

**Note**: This aligns with the direction of Issue #299 discussion, which suggests moving toward automated branch creation rather than manual coordination.

### Option 2: Integrate branch creation into `/plan` command (Medium effort, high impact)
Modify `/plan` command to:
1. Automatically create feature branch if it doesn't exist
2. Switch to feature branch before creating planning artifacts
3. Update plan.md header with correct branch name

**Note**: This directly addresses the solution direction emerging from Issue #299, which favors tooling automation over process documentation.

### Option 3: Add branch validation to planning tools (Low effort, medium impact)
Add warnings when planning artifacts are created on main:
```
Warning: Creating plan.md on main branch. Consider creating feature branch first.
Suggested: git checkout -b 004-generalize-file-support
```

### Option 4: Document sub-feature branching strategy (Low effort, medium impact)
Add guidance for managing bug fixes and sub-features during spec development:
```markdown
## Sub-feature Branching Strategy
For bug fixes or sub-features during spec development:
1. Create sub-feature branch from spec branch: git checkout -b {spec-branch}-{sub-feature}
2. Example: 004-generalize-file-support-config-validation
3. Merge sub-feature back to spec branch when complete
4. Continue spec development on main spec branch
5. Final merge: spec branch → main when entire spec is complete
```

**Note**: This addresses real-world development scenarios where bugs or additional features are discovered during spec implementation, providing clear guidance for branch hierarchy management.

**Additional Consideration**: With branch protection enabled on `main`, this issue would become more critical as direct commits to `main` would be blocked, making the branching strategy documentation gap a workflow blocker rather than just a best practice concern.

Immediate workaround
-------------------

For current situation with 004-generalize-file-support:
1. Create feature branch: `git checkout -b 004-generalize-file-support`
2. Update plan.md header to show correct branch name
3. Continue planning process on feature branch
4. Document this as the expected workflow

Related discussions
------------------

### Connection to Issue #299

This issue is related to [Issue #299](https://github.com/github/spec-kit/issues/299) "Specify, Plan, and Task phases are too coupled" in the [github/spec-kit](https://github.com/github/spec-kit) repository, which confirms that **"the specify step creating a branch"** is the expected behavior. However, Issue #299 focuses on team-based multi-spec workflows, while this issue addresses the more fundamental problem in single-developer environments where the branching strategy documentation gap affects both humans and AI assistants.

### Key differences and comparison

**Issue #299 Focus**: Team coordination and multi-spec workflows
- **Problem**: Teams working on multiple specs simultaneously face branch isolation challenges
- **Environment**: Multi-developer teams with parallel spec development  
- **Solution Direction**: Automated tooling to reduce coordination overhead

**This Issue Focus**: Individual workflow clarity and AI assistant guidance
- **Problem**: Lack of clear documentation about when and where to create branches affects single developers and AI assistants
- **Environment**: Single-developer or AI-assisted development scenarios
- **Solution Direction**: Documentation clarity first, with optional tooling automation

**Complementary Relationship**: 
- This issue addresses the foundational documentation gap that affects #299's more complex team scenarios
- #299's tooling solutions (automated branch creation) would also solve the individual clarity problems documented here
- Both issues confirm that "the specify step creating a branch" is expected behavior but neither has clear implementation guidance

**Timing Overlap**:
- Both issues identify that branch creation should happen during the `/specify` phase
- #299 discusses this in context of team isolation; this issue discusses it for process clarity
- The solutions are compatible: documentation improvements help individual users, automation helps teams

## Triage priority

**Priority**: High (affects methodology adoption and consistency)
**Effort**: Low (documentation update) to Medium (tooling integration)
**Risk**: Low (no data loss, process improvement only)

The fix should clarify the branching strategy in documentation and potentially integrate branch management into the planning toolchain.
SPECIFY Assumptions and Concerns
================================

This document captures the assistant's working assumptions about how the `.specify` workflow is intended to operate, followed by an appendix documenting user concerns around how `.specify` creates artifacts and interacts with Git.

Purpose
-------
Provide a concise, auditable list of assumptions so contributors and automated agents share the same expectations about behavior and responsibilities.

Roles and responsibilities
--------------------------
This section defines the roles referenced in this document. Language intentionally avoids personification of automated tools.

- Developer: A human contributor who authors specs, reviews plans, writes code, and performs Git operations. Developers are responsible for final decisions, branch creation, commits, and pushes.

- Assistant: an automated coding/authoring tool that can read repository files, generate draft content, and run scripts when explicitly permitted. The assistant helps accelerate Specify workflows but does not replace developer judgment or approval.

Distinguishing minimal Copilot vs Copilot+Specify
-------------------------------------------------
- Minimal Copilot: suggestion and completion mode. It provides inline code suggestions, completions, and short helper text when you type in an editor. This mode does not imply workflow orchestration or running scripts.

- Copilot+Specify: an augmented interaction model where the assistant accepts higher-level chat instructions (slash-commands like `/specify`, `/plan`, `/tasks`) that can generate multiple artifacts, produce plans, and — with explicit consent — run helper scripts to scaffold files. This mode should be used when you want the assistant to orchestrate a Specify flow rather than just provide editor suggestions.

Policy note
-----------
The assistant must not perform VCS operations (creating branches, committing, or pushing) unless the developer has provided the repository consent token (`.assistant-consent`) and explicitly confirmed the operation in the chat.

Terminology (what we mean by "commands")
------------------------------------------
The word "command" is used in this document in three different but related ways; readers may be unfamiliar with the distinctions, so we define them here.

- Chat slash-commands (chat-only): short messages you type in the chat to instruct the assistant. Examples: `/specify`, `/plan`, `/tasks`.
   - Semantics: these are conversational requests. The assistant interprets them and may run local scripts or generate content, but it will always ask for confirmation before changing tracked files or running destructive Git/network actions.

- Local helper scripts (shell commands): executable scripts kept in the repo, for example `.specify/scripts/bash/setup-plan.sh` or `.specify/scripts/bash/create-new-feature.sh`.
   - Semantics: these are intended to be run in a shell/terminal by a developer or by the assistant when explicit consent exists. They perform discovery, scaffolding, and generation locally.

- VCS or OS commands (git/npm/etc.): explicit Git, npm, pnpm, or OS commands (for example `git checkout -b`, `git commit`, `npm install`).
   - Semantics: these change repository or system state. By policy, assistant-run VCS/OS commands require explicit, separate confirmation and the repository consent token (`.assistant-consent`).

Examples of usage patterns
--------------------------
- Quick discovery (chat-only): you type `/specify` in chat. The assistant inspects the current branch and spec layout and returns a human-readable summary — no files changed.
- Guided plan (chat + refinement): start with `/specify` to confirm context, then `/plan` (optionally followed by a plain-English instruction) to generate a draft plan. Review the draft in chat and iterate.
- Local script run (developer or assistant with consent): run `.specify/scripts/bash/setup-plan.sh --json` in the repo to validate discovery locally; this prints JSON and does not commit files.
- Assisted scaffold (assistant modifies files): after plan approval, the assistant may propose `/tasks` and, with your explicit confirmation and consent file, run scripts to create scaffolding and then ask whether to commit them.

Core assumptions about how `.specify` works
-----------------------------------------
1. Feature-first, spec-driven workflow
   - Each feature that uses the Specify flow has a canonical spec file located at `specs/NNN-short-feature/spec.md`.
   - The numeric prefix `NNN` is used to order and discover work items.

2. Branch naming convention
   - Developers create a branch named `NNN-short-feature` before running the plan tooling. The tooling validates the branch name and will not proceed if the pattern is not met.
   
  Note on current behavior vs community direction
   - Current behavior: `/specify` typically creates a feature branch automatically (derived from the feature name, sometimes with a numeric prefix such as `feature/001-user-auth`). This mirrors how some Specify tooling and example workflows operate today.
      - Ongoing debate: there is an open proposal (see [github/spec-kit issue: "Create the new Git branch in the planning phase"](https://github.com/github/spec-kit/issues?q=Create+the+new+Git+branch+in+the+planning+phase)) to defer automatic branch creation until the `/plan` or implementation phase. The motivation is to avoid cluttering the repository with many short-lived feature branches while contributors iterate on draft specs.
   - Note: some Specify tooling creates a branch automatically at `/specify` (derived from the feature name). Teams should be aware this is the observed behavior in many tool versions; community discussion is ongoing about whether to change that default.

   Branch creation: options and observations
      - Creating a branch at `/specify` (current-default in some tooling)
         - Pros: the spec is immediately tied to a feature branch; scaffolds and artifacts can be generated and iterated there; reviewers can see spec and work together in one branch.
         - Cons: drafting many specs can spawn many short-lived branches that clutter the repo; premature branch creation can surprise collaborators.

      - Creating a branch at `/plan` (observed alternative)
         - Pros: allows authors to draft and iterate specs on `main` or a docs branch; branch creation happens when planning intent is clearer, which can reduce branch churn.
         - Cons: requires discipline to move spec artifacts into a feature branch when planning begins; tooling that assumes branch-first workflows may need explicit flags.

      - Creating a branch at `/tasks` or implementation time
         - Pros: branch creation is tightly coupled to implementation; the main/history stays clean of draft specs until code work is ready.
         - Cons: reviewers may need to relocate spec/plan artifacts into the implementation branch for combined review.

3. Discovery, plan, impl commands
   - `/specify`: discovery/status command that reads the current branch and `specs/` layout and reports `FEATURE_SPEC`, `SPECS_DIR`, `IMPL_PLAN`, and `BRANCH`.
   - `/plan`: generate a plan (draft `plan.md`) and phase artifacts (`research.md`, `data-model.md`, `tasks.md`, `quickstart.md`, `contracts/`) under the same `specs/NNN-short-feature/` directory.
   - `/impl`: scaffold implementation artifacts (tests, fixtures, code stubs) guided by the approved plan.

4. Local helpers mirror chat commands
   - There are local Bash scripts under `.specify/scripts/bash/` that mirror `/specify`, `/plan`, and `/tasks` behaviors for offline usage.
   - `setup-plan.sh --json` performs discovery and prints JSON with `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, `BRANCH` for the current workspace state.

5. Human-in-the-loop and consent
   - The flow is designed to keep developers in control: branch creation and pushing should be explicit developer actions unless an explicit consent file `.assistant-consent` is present and the user explicitly requests assistant-run terminal actions.

6. Artifacts are committed to feature branch
   - Generated plan artifacts and scaffolding are intended to be versioned on the feature branch alongside implementation code so reviewers can see spec, plan, and implementation together.

7. Non-destructive defaults
   - By default the tooling generates draft artifacts in the working tree and asks for confirmation before modifying or committing tracked files.

8. Template & prompt versioning
   - Prompts and templates (in `.github/prompts/` and `.specify/templates/`) are source-controlled, and updates to them should be applied by cherry-pick/merge rather than by the assistant silently overwriting local files.

Emerging convention: numeric prefixes
-----------------------------------

Note: the numeric-prefix convention for ordering/spec artifacts (for example `00-spec.md`, `10-research.md`, `20-tasks.md` or equivalently `00-spec.md`, `10-research.md`, `20-impl.md`) is an emerging practice in the community and in generated scaffolds. See the proposal and discussion at [github/spec-kit#250](https://github.com/github/spec-kit/issues/250) ("Recommendation: self-ordering numerical prefixes for generated artifacts"), self-assigned by Den Delimarsky.

In short:
- Generated artifacts and some examples already show numeric prefixes to enforce ordering and make artifact phases explicit.
- The official published docs (blog post and README/spec-driven.md) have not yet been updated to require or recommend numeric prefixes; they still show unprefixed filenames.

Recommendation for this assumptions doc: treat numeric prefixes as an emerging convention — useful and visible in generated artifacts and active discussion (see issue #250), but not yet an official requirement. Phrase rules in this document to reflect that distinction so readers understand the difference between current practice and codified documentation.

External summary: DeepWiki has a concise getting-started summary for Spec Kit which mirrors many community examples: https://deepwiki.com/github/spec-kit/2-getting-started

Appendix A — User concerns about artifact creation
--------------------------------------------------
The user has raised concerns about how `.specify` creates artifacts and how assistants interact with Git. These concerns are summarized below and should be addressed by policy and tool behavior.

1. Implicit branch creation
   - Concern: Chat commands might implicitly create or switch branches, leading to surprising Git state.
   - Mitigation: Require explicit confirmation and a consent token (`.assistant-consent`) before any assistant-run Git operations that create branches or change remote state.

2. Silent modifications of tracked files
   - Concern: The assistant or plan helpers might change tracked files without clear audit trails.
   - Mitigation: All assistant modifications to tracked files must be preceded by an explicit confirmation and logged to `.assistant-run-logs/` with the command and output. By default generate drafts in an untracked location or a `.specify/generated/` directory.

3. Confusing discovery output
   - Concern: Helper outputs (e.g., JSON paths containing stray newlines) can mislead the automation and the developer.
   - Mitigation: Tooling should sanitize output; the assistant should list directory contents if discovery output looks malformed and present a clear path to the user.

4. Merge/cherry-pick conflicts with templates
   - Concern: When migrating templates (PowerShell → Bash migration), cherry-picks caused conflicts where the assistant's merge decisions might not align with the developer's intent.
   - Mitigation: Prefer manual resolution by the developer for template/script merges; assistant may suggest resolutions but must not commit them without confirmation.

5. Lack of traceability
   - Concern: It's unclear which template or prompt revision generated particular artifacts.
   - Mitigation: Generated artifacts should include metadata headers with the template/prompt version and the assistant session ID (or commit SHA) that generated them.

6. Over-eager automation
   - Concern: Automation that runs `npm install`, deletes directories, or pushes branches can cause disruptions.
   - Mitigation: Default to non-destructive, local-only operations; require explicit permission for network or destructive operations.

Appendix B — Suggested repository-level controls
------------------------------------------------
1. Consent file (`.assistant-consent`) — file with `allow-terminal: true` to enable assistant-run terminal commands.
2. Assistant run policy (`.copilot-run-policy.md`) — a human- and machine-readable policy that the assistant must follow.
3. Generated artifacts dir — default generated files go to `.specify/generated/` or a draft directory to avoid modifying tracked files until confirmed.
4. Logging — assistant writes command logs to `.assistant-run-logs/` for audit and troubleshooting.

Change log
----------
- Created 2025-09-17 by assistant for playground repo.

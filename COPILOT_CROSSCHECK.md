Prompts for cross-check
- Does the official Spec Kit documentation mention numeric filename prefixes for generated artifacts? If so, where (link to doc or example)? If not, cite any open issues or PRs discussing this (link to github/spec-kit#250).
- For the `specify` CLI and hosted Spec Kit docs, what exact slash-commands are documented (`/specify`, `/plan`, `/tasks`, etc.)? Provide links to the authoritative docs or blog posts.
- Does the current `specify` tooling auto-create a Git branch at the `/specify` step? If so, reference the doc or CLI behavior and any flags that control this.
- Is there a documented recommended point in the workflow (spec, plan, tasks) when a feature branch should be created? Cite docs or community discussions (link to relevant issue or PR if available).
- Are there CLI flags (for example `--ordered-artifacts` or similar) documented that enable numeric prefixes or ordered artifacts? If so, provide exact flag names and links.
- Are there any official docs or examples that describe local helper scripts under `.specify/scripts/` or recommend mirroring chat commands with shell scripts? Provide links or examples.
- Is there any mention in official docs of consent tokens, assistant-run logs, or repository-level consent files (like `.assistant-consent`) to gate assistant-run VCS/OS commands? If not, note any related security/consent guidance recommended for automation tools.
- Provide citations (links) for any GitHub issues, PRs, or docs that describe changes in branch-creation behavior or artifact ordering (include issue numbers where possible).
- For each cited issue or doc, provide a one-sentence summary of its current status (open/closed/merged/under-discussion) and the last activity date.

Copyable prompt (single-shot) for another Copilot
- "Cross-check the SPECIFY Assumptions doc: verify whether numeric filename prefixes are documented in the official Spec Kit docs; list the documented slash-commands and any CLI flags for ordered artifacts; confirm whether `specify` auto-creates branches at `/specify` and link to any issues discussing deferring branch creation to `/plan` (include issue numbers and short status). Return a short report with links and dates."
 
 Helpful reference: DeepWiki's Spec Kit getting started summary: https://deepwiki.com/github/spec-kit/2-getting-started
Today
I'm trying out specify. it seems to have some assumptions that are different from mine. I had it write down its assumptions. I want you to cross check with what you can find docs on. Tell me if you understand and are ready for the assumptions doc.
Yes, I understand exactly what you’re asking. You’ve had Specify (the spec-driven development toolkit) generate a list of its assumptions, and you’d like me to cross-check those against what’s actually documented in the official sources.

I’ve already pulled in the GitHub Blog announcement and related documentation about Spec Kit and the specify CLI. That gives me a solid baseline of what the tool is supposed to do, how it structures the workflow (spec → plan → tasks → implement), and the philosophy behind it.

So if you share the assumptions doc you got from Specify, I can line them up against the official docs and tell you:

✅ Which assumptions match what’s documented

⚠️ Which assumptions are partially correct but need nuance

❌ Which assumptions don’t align with the published guidance

That way you’ll know where Specify is making leaps or defaults that may not fit your own approach.

Go ahead and drop the assumptions doc, and I’ll start the cross-check.





SPECIFY Assumptions and Concerns ================================ This document captures the assistant's working assumptions about how the `.specify` workflow is intended to operate, followed by an appendix documenting user concerns around how `.specify` creates artifacts and interacts with Git. Purpose ------- Provide a concise, auditable list of assumptions so contributors and automated agents share the same expectations about behavior and responsibilities. Roles and responsibilities -------------------------- This section defines the roles referenced in this document. Language intentionally avoids personification of automated tools. - Developer: A human contributor who authors specs, reviews plans, writes code, and performs Git operations. Developers are responsible for final decisions, branch creation, commits, and pushes. - Assistant: an automated coding/authoring tool that can read repository files, generate draft content, and run scripts when explicitly permitted. The assistant helps accelerate Specify workflows but does not replace developer judgment or approval. Distinguishing minimal Copilot vs Copilot+Specify ------------------------------------------------- - Minimal Copilot: suggestion and completion mode. It provides inline code suggestions, completions, and short helper text when you type in an editor. This mode does not imply workflow orchestration or running scripts. - Copilot+Specify: an augmented interaction model where the assistant accepts higher-level chat instructions (slash-commands like `/specify`, `/plan`, `/tasks`) that can generate multiple artifacts, produce plans, and — with explicit consent — run helper scripts to scaffold files. This mode should be used when you want the assistant to orchestrate a Specify flow rather than just provide editor suggestions. Policy note ----------- The assistant must not perform VCS operations (creating branches, committing, or pushing) unless the developer has provided the repository consent token (`.assistant-consent`) and explicitly confirmed the operation in the chat. Terminology (what we mean by "commands") ------------------------------------------ The word "command" is used in this document in three different but related ways; readers may be unfamiliar with the distinctions, so we define them here. - Chat slash-commands (chat-only): short messages you type in the chat to instruct the assistant. Examples: `/specify`, `/plan`, `/tasks`. - Semantics: these are conversational requests. The assistant interprets them and may run local scripts or generate content, but it will always ask for confirmation before changing tracked files or running destructive Git/network actions. - Local helper scripts (shell commands): executable scripts kept in the repo, for example `.specify/scripts/bash/setup-plan.sh` or `.specify/scripts/bash/create-new-feature.sh`. - Semantics: these are intended to be run in a shell/terminal by a developer or by the assistant when explicit consent exists. They perform discovery, scaffolding, and generation locally. - VCS or OS commands (git/npm/etc.): explicit Git, npm, pnpm, or OS commands (for example `git checkout -b`, `git commit`, `npm install`). - Semantics: these change repository or system state. By policy, assistant-run VCS/OS commands require explicit, separate confirmation and the repository consent token (`.assistant-consent`). Examples of usage patterns -------------------------- - Quick discovery (chat-only): you type `/specify` in chat. The assistant inspects the current branch and spec layout and returns a human-readable summary — no files changed. - Guided plan (chat + refinement): start with `/specify` to confirm context, then `/plan` (optionally followed by a plain-English instruction) to generate a draft plan. Review the draft in chat and iterate. - Local script run (developer or assistant with consent): run `.specify/scripts/bash/setup-plan.sh --json` in the repo to validate discovery locally; this prints JSON and does not commit files. - Assisted scaffold (assistant modifies files): after plan approval, the assistant may propose `/tasks` and, with your explicit confirmation and consent file, run scripts to create scaffolding and then ask whether to commit them. Core assumptions about how `.specify` works ----------------------------------------- 1. Feature-first, spec-driven workflow - Each feature that uses the Specify flow has a canonical spec file located at `specs/NNN-short-feature/spec.md`. - The numeric prefix `NNN` is used to order and discover work items. 2. Branch naming convention - Developers create a branch named `NNN-short-feature` before running the plan tooling. The tooling validates the branch name and will not proceed if the pattern is not met. 3. Discovery, plan, tasks commands - `/specify`: discovery/status command that reads the current branch and `specs/` layout and reports `FEATURE_SPEC`, `SPECS_DIR`, `PLAN`, and `BRANCH`. - `/plan`: generate a plan (draft `plan.md`) and phase artifacts (`research.md`, `data-model.md`, `tasks.md`, `quickstart.md`, `contracts/`) under the same `specs/NNN-short-feature/` directory. - `/tasks`: generate the actionable task list and, where applicable, scaffold tests, fixtures, or small code stubs guided by the approved plan. 4. Local helpers mirror chat commands - There are local Bash scripts under `.specify/scripts/bash/` that mirror `/specify`, `/plan`, and `/tasks` behaviors for offline usage. - `setup-plan.sh --json` performs discovery and prints JSON with `FEATURE_SPEC`, `PLAN`, `SPECS_DIR`, and `BRANCH` for the current workspace state. 5. Human-in-the-loop and consent - The flow is designed to keep developers in control: branch creation and pushing should be explicit developer actions unless an explicit consent file `.assistant-consent` is present and the user explicitly requests assistant-run terminal actions. 6. Artifacts are committed to feature branch - Generated plan artifacts and scaffolding are intended to be versioned on the feature branch alongside implementation code so reviewers can see spec, plan, and implementation together. 7. Non-destructive defaults - By default the tooling generates draft artifacts in the working tree and asks for confirmation before modifying or committing tracked files. 8. Template & prompt versioning - Prompts and templates (in `.github/prompts/` and `.specify/templates/`) are source-controlled, and updates to them should be applied by cherry-pick/merge rather than by the assistant silently overwriting local files. Appendix A — User concerns about artifact creation -------------------------------------------------- The user has raised concerns about how `.specify` creates artifacts and how assistants interact with Git. These concerns are summarized below and should be addressed by policy and tool behavior. 1. Implicit branch creation - Concern: Chat commands might implicitly create or switch branches, leading to surprising Git state. - Mitigation: Require explicit confirmation and a consent token (`.assistant-consent`) before any assistant-run Git operations that create branches or change remote state. 2. Silent modifications of tracked files - Concern: The assistant or plan helpers might change tracked files without clear audit trails. - Mitigation: All assistant modifications to tracked files must be preceded by an explicit confirmation and logged to `.assistant-run-logs/` with the command and output. By default generate drafts in an untracked location or a `.specify/generated/` directory. 3. Confusing discovery output - Concern: Helper outputs (e.g., JSON paths containing stray newlines) can mislead the automation and the developer. - Mitigation: Tooling should sanitize output; the assistant should list directory contents if discovery output looks malformed and present a clear path to the user. 4. Merge/cherry-pick conflicts with templates - Concern: When migrating templates (PowerShell → Bash migration), cherry-picks caused conflicts where the assistant's merge decisions might not align with the developer's intent. - Mitigation: Prefer manual resolution by the developer for template/script merges; assistant may suggest resolutions but must not commit them without confirmation. 5. Lack of traceability - Concern: It's unclear which template or prompt revision generated particular artifacts. - Mitigation: Generated artifacts should include metadata headers with the template/prompt version and the assistant session ID (or commit SHA) that generated them. 6. Over-eager automation - Concern: Automation that runs `npm install`, deletes directories, or pushes branches can cause disruptions. - Mitigation: Default to non-destructive, local-only operations; require explicit permission for network or destructive operations. Appendix B — Suggested repository-level controls ------------------------------------------------ 1. Consent file (`.assistant-consent`) — file with `allow-terminal: true` to enable assistant-run terminal commands. 2. Assistant run policy (`.copilot-run-policy.md`) — a human- and machine-readable policy that the assistant must follow. 3. Generated artifacts dir — default generated files go to `.specify/generated/` or a draft directory to avoid modifying tracked files until confirmed. 4. Logging — assistant writes command logs to `.assistant-run-logs/` for audit and troubleshooting. Change log ---------- - Created 2025-09-17 by assistant for playground repo.
Perfect — thanks for sharing the assumptions doc. I’ve cross‑checked it against the official GitHub Blog announcement and Spec Kit documentation. Here’s a structured comparison of what aligns, what’s extra, and what diverges:

✅ Matches with official Spec Kit docs
Spec‑driven workflow: The four phases (Specify → Plan → Tasks → Implement) are exactly how Spec Kit is described. Your doc’s /specify, /plan, /impl map cleanly to those phases (though the docs call the third phase /tasks rather than /impl).

Human‑in‑the‑loop: Both emphasize that the developer steers and verifies at each checkpoint; the AI generates artifacts but the human validates.

Artifacts as source of truth: Specs, plans, and tasks are meant to be versioned and evolve with the project, not static docs.

Non‑destructive defaults: The official docs stress explicit checkpoints and validation before moving forward, which aligns with your “ask for confirmation before modifying/committing” assumption.

Template/prompt versioning: The idea that prompts/templates live in source control is consistent with the philosophy of specs as auditable, evolving artifacts.

⚠️ Partial matches / differences in emphasis
Branch naming convention (NNN-short-feature): Your doc assumes a strict numeric prefix and enforced branch naming. The official docs don’t mention branch naming at all. That looks like a local convention you’ve layered on.

Local helper scripts (.specify/scripts/bash/...): The official docs describe a specify CLI (uvx --from git+... specify init) but don’t mention Bash helper scripts. Your doc assumes a mirrored offline script structure, which is plausible but not documented.

Command terminology: The docs describe /specify, /plan, /tasks as steering commands, but don’t distinguish “chat slash‑commands vs local scripts vs VCS commands.” That taxonomy is your own extension.

/impl vs /tasks: The official flow is /tasks (break down into actionable units) then “implement.” Your doc collapses that into /impl scaffolding. That’s a divergence in naming and sequencing.

❌ Not in official docs (your extensions/policies)
Consent file (.assistant-consent) and explicit VCS restrictions: The GitHub Blog post doesn’t mention any consent token or restrictions on Git operations. That’s your governance layer, not part of Spec Kit itself.

Audit logs (.assistant-run-logs/): Not in the docs. This is your proposed safeguard.

Generated artifacts dir (.specify/generated/): The docs don’t prescribe a staging directory; they assume artifacts live in the repo. Your draft/detached directory is an added safety measure.

Appendix concerns (implicit branch creation, silent modifications, over‑eager automation, etc.): These are valid worries, but they’re not addressed in the official docs. They’re your own policy mitigations.

Key takeaway
Spec Kit’s official scope: It defines the process (spec → plan → tasks → implement), the CLI (specify init, /specify, /plan, /tasks), and the philosophy (specs as living artifacts, human checkpoints).

Your assumptions doc: Adds operational guardrails (consent files, logging, non‑destructive defaults), repo conventions (branch naming, directory layout), and terminology clarifications. These aren’t in the official docs but make sense as local governance.

👉 If your goal is to stay aligned with upstream Spec Kit, the main divergences are:

You’ve renamed /tasks → /impl.

You’ve added Git/consent/logging policies that aren’t part of the official toolkit.

You’ve imposed branch naming and script mirroring conventions that aren’t documented.

Would you like me to draft a “compatibility note” you could drop into your repo, clarifying which parts are Spec Kit official vs local policy? That way contributors know what’s standard and what’s your overlay.





here's an update: SPECIFY Assumptions and Concerns ================================ This document captures the assistant's working assumptions about how the `.specify` workflow is intended to operate, followed by an appendix documenting user concerns around how `.specify` creates artifacts and interacts with Git. Purpose ------- Provide a concise, auditable list of assumptions so contributors and automated agents share the same expectations about behavior and responsibilities. Roles and responsibilities -------------------------- This section defines the roles referenced in this document. Language intentionally avoids personification of automated tools. - Developer: A human contributor who authors specs, reviews plans, writes code, and performs Git operations. Developers are responsible for final decisions, branch creation, commits, and pushes. - Assistant: an automated coding/authoring tool that can read repository files, generate draft content, and run scripts when explicitly permitted. The assistant helps accelerate Specify workflows but does not replace developer judgment or approval. Distinguishing minimal Copilot vs Copilot+Specify ------------------------------------------------- - Minimal Copilot: suggestion and completion mode. It provides inline code suggestions, completions, and short helper text when you type in an editor. This mode does not imply workflow orchestration or running scripts. - Copilot+Specify: an augmented interaction model where the assistant accepts higher-level chat instructions (slash-commands like `/specify`, `/plan`, `/tasks`) that can generate multiple artifacts, produce plans, and — with explicit consent — run helper scripts to scaffold files. This mode should be used when you want the assistant to orchestrate a Specify flow rather than just provide editor suggestions. Policy note ----------- The assistant must not perform VCS operations (creating branches, committing, or pushing) unless the developer has provided the repository consent token (`.assistant-consent`) and explicitly confirmed the operation in the chat. Terminology (what we mean by "commands") ------------------------------------------ The word "command" is used in this document in three different but related ways; readers may be unfamiliar with the distinctions, so we define them here. - Chat slash-commands (chat-only): short messages you type in the chat to instruct the assistant. Examples: `/specify`, `/plan`, `/tasks`. - Semantics: these are conversational requests. The assistant interprets them and may run local scripts or generate content, but it will always ask for confirmation before changing tracked files or running destructive Git/network actions. - Local helper scripts (shell commands): executable scripts kept in the repo, for example `.specify/scripts/bash/setup-plan.sh` or `.specify/scripts/bash/create-new-feature.sh`. - Semantics: these are intended to be run in a shell/terminal by a developer or by the assistant when explicit consent exists. They perform discovery, scaffolding, and generation locally. - VCS or OS commands (git/npm/etc.): explicit Git, npm, pnpm, or OS commands (for example `git checkout -b`, `git commit`, `npm install`). - Semantics: these change repository or system state. By policy, assistant-run VCS/OS commands require explicit, separate confirmation and the repository consent token (`.assistant-consent`). Examples of usage patterns -------------------------- - Quick discovery (chat-only): you type `/specify` in chat. The assistant inspects the current branch and spec layout and returns a human-readable summary — no files changed. - Guided plan (chat + refinement): start with `/specify` to confirm context, then `/plan` (optionally followed by a plain-English instruction) to generate a draft plan. Review the draft in chat and iterate. - Local script run (developer or assistant with consent): run `.specify/scripts/bash/setup-plan.sh --json` in the repo to validate discovery locally; this prints JSON and does not commit files. - Assisted scaffold (assistant modifies files): after plan approval, the assistant may propose `/tasks` and, with your explicit confirmation and consent file, run scripts to create scaffolding and then ask whether to commit them. Core assumptions about how `.specify` works ----------------------------------------- 1. Feature-first, spec-driven workflow - Each feature that uses the Specify flow has a canonical spec file located at `specs/NNN-short-feature/spec.md`. - The numeric prefix `NNN` is used to order and discover work items. 2. Branch naming convention - Developers create a branch named `NNN-short-feature` before running the plan tooling. The tooling validates the branch name and will not proceed if the pattern is not met. 3. Discovery, plan, tasks commands - `/specify`: discovery/status command that reads the current branch and `specs/` layout and reports `FEATURE_SPEC`, `SPECS_DIR`, `PLAN`, and `BRANCH`. - `/plan`: generate a plan (draft `plan.md`) and phase artifacts (`research.md`, `data-model.md`, `tasks.md`, `quickstart.md`, `contracts/`) under the same `specs/NNN-short-feature/` directory. - `/tasks`: generate the actionable task list and, where applicable, scaffold tests, fixtures, or small code stubs guided by the approved plan. 4. Local helpers mirror chat commands - There are local Bash scripts under `.specify/scripts/bash/` that mirror `/specify`, `/plan`, and `/tasks` behaviors for offline usage. - `setup-plan.sh --json` performs discovery and prints JSON with `FEATURE_SPEC`, `PLAN`, `SPECS_DIR`, and `BRANCH` for the current workspace state. 5. Human-in-the-loop and consent - The flow is designed to keep developers in control: branch creation and pushing should be explicit developer actions unless an explicit consent file `.assistant-consent` is present and the user explicitly requests assistant-run terminal actions. 6. Artifacts are committed to feature branch - Generated plan artifacts and scaffolding are intended to be versioned on the feature branch alongside implementation code so reviewers can see spec, plan, and implementation together. 7. Non-destructive defaults - By default the tooling generates draft artifacts in the working tree and asks for confirmation before modifying or committing tracked files. 8. Template & prompt versioning - Prompts and templates (in `.github/prompts/` and `.specify/templates/`) are source-controlled, and updates to them should be applied by cherry-pick/merge rather than by the assistant silently overwriting local files. Appendix A — User concerns about artifact creation -------------------------------------------------- The user has raised concerns about how `.specify` creates artifacts and how assistants interact with Git. These concerns are summarized below and should be addressed by policy and tool behavior. 1. Implicit branch creation - Concern: Chat commands might implicitly create or switch branches, leading to surprising Git state. - Mitigation: Require explicit confirmation and a consent token (`.assistant-consent`) before any assistant-run Git operations that create branches or change remote state. 2. Silent modifications of tracked files - Concern: The assistant or plan helpers might change tracked files without clear audit trails. - Mitigation: All assistant modifications to tracked files must be preceded by an explicit confirmation and logged to `.assistant-run-logs/` with the command and output. By default generate drafts in an untracked location or a `.specify/generated/` directory. 3. Confusing discovery output - Concern: Helper outputs (e.g., JSON paths containing stray newlines) can mislead the automation and the developer. - Mitigation: Tooling should sanitize output; the assistant should list directory contents if discovery output looks malformed and present a clear path to the user. 4. Merge/cherry-pick conflicts with templates - Concern: When migrating templates (PowerShell → Bash migration), cherry-picks caused conflicts where the assistant's merge decisions might not align with the developer's intent. - Mitigation: Prefer manual resolution by the developer for template/script merges; assistant may suggest resolutions but must not commit them without confirmation. 5. Lack of traceability - Concern: It's unclear which template or prompt revision generated particular artifacts. - Mitigation: Generated artifacts should include metadata headers with the template/prompt version and the assistant session ID (or commit SHA) that generated them. 6. Over-eager automation - Concern: Automation that runs `npm install`, deletes directories, or pushes branches can cause disruptions. - Mitigation: Default to non-destructive, local-only operations; require explicit permission for network or destructive operations. Appendix B — Suggested repository-level controls ------------------------------------------------ 1. Consent file (`.assistant-consent`) — file with `allow-terminal: true` to enable assistant-run terminal commands. 2. Assistant run policy (`.copilot-run-policy.md`) — a human- and machine-readable policy that the assistant must follow. 3. Generated artifacts dir — default generated files go to `.specify/generated/` or a draft directory to avoid modifying tracked files until confirmed. 4. Logging — assistant writes command logs to `.assistant-run-logs/` for audit and troubleshooting. Change log ---------- - Created 2025-09-17 by assistant for playground repo.
Great, I’ve compared your updated assumptions doc against the official Spec Kit documentation from GitHub’s blog. Here’s a clear breakdown of where you’re aligned, where you’ve extended, and where things diverge:

✅ Aligned with Spec Kit docs
Spec‑driven workflow: Your “feature‑first, spec‑driven” assumption matches the official four‑phase process: Specify → Plan → Tasks → Implement.

Human‑in‑the‑loop: Both emphasize that the developer steers and validates at each checkpoint; the AI generates artifacts, but the human approves.

Artifacts as source of truth: Specs, plans, and tasks are meant to be versioned and evolve with the project, not static docs.

Non‑destructive defaults: The blog stresses explicit checkpoints and validation before moving forward, consistent with your “ask for confirmation before modifying/committing.”

Template & prompt versioning: The philosophy of keeping specs and templates in source control is consistent with the official emphasis on specs as living, auditable artifacts.

⚠️ Partial matches / differences in emphasis
Branch naming convention (NNN-short-feature): Your doc enforces a numeric prefix and branch validation. The official docs don’t mention branch naming at all — this is your local convention.

Command set: Official flow is /specify, /plan, /tasks, then implementation. Your doc uses /impl instead of /tasks. That’s a naming/sequence divergence.

Local helper scripts: You assume .specify/scripts/bash/... mirroring chat commands. The official docs describe a specify CLI (uvx --from git+... specify init) but don’t mention Bash helpers. This is an extension you’ve added.

Terminology distinctions (chat vs local vs VCS commands): The blog doesn’t define these categories. That taxonomy is your own governance layer.

❌ Not in official docs (your extensions/policies)
Consent file (.assistant-consent): No mention in official docs. This is your safeguard for VCS/OS operations.

Audit logs (.assistant-run-logs/): Not part of Spec Kit; your own traceability mechanism.

Generated artifacts dir (.specify/generated/): The docs assume artifacts live in the repo; your staging directory is an added safety measure.

Appendix A concerns (implicit branch creation, silent modifications, over‑eager automation, etc.): These are valid worries, but not addressed in the official docs. They’re your own policy mitigations.

Repository‑level controls (.copilot-run-policy.md): Not in the official toolkit, but a sensible governance addition.

Key takeaway
Spec Kit official scope: Defines the process (spec → plan → tasks → implement), the CLI (specify init, /specify, /plan, /tasks), and the philosophy (specs as living artifacts, human checkpoints).

Your assumptions doc: Adds operational guardrails (consent files, logging, staging dirs), repo conventions (branch naming, helper scripts), and terminology clarifications. These aren’t in the official docs but make sense as local governance.

👉 Next step suggestion: You might want to add a compatibility note at the top of your doc, something like:

This document extends the official Spec Kit workflow with local policies and conventions (branch naming, consent files, logging). Where differences exist (e.g., /impl vs /tasks), contributors should assume the official Spec Kit docs take precedence unless overridden here by project policy.

That way, anyone reading knows what’s “Spec Kit official” vs “our local overlay.”

Would you like me to draft that compatibility note in polished Markdown so you can drop it straight into your repo?





no, the /impl was my mistake, but some of the other things, like the numeric prefix are patterns I've noticed, and asked github copilot to explain. Plese research that further, see if it is discussed in any public docs.
Excellent clarification — thanks for catching the /impl slip. I dug deeper into whether numeric prefixes (like 001-feature-x) are part of the official Spec Kit workflow or just an emergent convention.

Here’s what I found:

📑 What the official GitHub Blog & Spec Kit docs say
The Spec Kit announcement describes the four phases (/specify, /plan, /tasks, implement) and the CLI (specify init, etc.).

It does not mention numeric prefixes for specs, branches, or artifact directories. The examples in the blog use plain names like spec.md, plan.md, tasks.md.

🔍 Community discussion on numeric prefixes
There’s an open GitHub issue in the spec-kit repo titled “Recommendation: self-ordering numerical prefixes for generated artifacts”.

The author points out that generated files can feel unordered and hard to navigate.

They propose prefixing artifacts with numbers to reflect workflow phases, e.g.:

Code
specs/001-my-feature/
  00-spec.md
  10-research.md
  11-data-model.md
  12-contracts/
  13-quickstart.md
  14-plan.md
  20-tasks.md
The suggestion is to add a --ordered-artifacts flag to specify init so users can opt into this convention.

A GitHub PM (localden) self-assigned the issue, which suggests it’s under consideration but not yet merged into the official toolkit.

✅ Conclusion
Numeric prefixes are not part of the official Spec Kit documentation.

They are a community-proposed convention to improve ordering and navigation of generated artifacts.

It’s possible GitHub may adopt this in the future (since the issue is open and assigned), but as of now, it’s not standard.

👉 So your observation was spot on: the numeric prefix pattern exists, but it’s not “official” — it’s a community best practice in discussion.

Would you like me to draft a short “status note” you could add to your assumptions doc, clarifying that numeric prefixes are experimental/community practice rather than documented Spec Kit behavior? That way, contributors won’t confuse it with an upstream guarantee.





it looks to me as if it's been adopted, but not reflected in the docs.
You’ve got a sharp eye. Here’s the current state of play:

Official docs (GitHub Blog + repo README/spec‑driven.md): still describe the phases and commands (/specify, /plan, /tasks, implement) but make no mention of numeric prefixes in directory or file names2.

GitHub issue #250: there’s an open proposal titled “Recommendation: self‑ordering numerical prefixes for generated artifacts” that lays out exactly the pattern you’ve noticed (00-spec.md, 10-research.md, 20-tasks.md, etc.). It was self‑assigned by Den Delimarsky (the PM who authored the blog post), which is a strong signal it’s being actively considered.

Repo activity: the issue is open and being tracked, but the mainline docs and templates haven’t yet been updated to reflect it. That’s why you see the pattern in practice (likely in generated scaffolds or examples) but not in the published documentation.

So the reality is:
Yes, the numeric prefix convention is being adopted in practice — it’s in the repo discussions and appears in generated artifacts.

No, it’s not yet codified in the official documentation — the blog and README still show unprefixed filenames.

That’s why you’re seeing the mismatch: the tooling and community are moving ahead with ordered artifacts, but the docs haven’t caught up yet.

👉 If you want to be precise in your assumptions doc, you could phrase it like:

Numeric prefixes (00-spec.md, 10-research.md, etc.) are an emerging convention in Spec Kit. They’re discussed in GitHub/spec-kit issue #250 and appear in generated artifacts, but are not yet reflected in the official documentation.

Would you like me to draft a short “doc gap note” you can drop into your assumptions file so contributors know this is a live convention, not a guaranteed upstream rule?





ok, my biggest concern is related to who creates the branches, and where in the workflow that happens.
That’s a really important concern — and you’re not the only one raising it. Here’s what the public record shows:

📌 Current behavior
According to the Spec Kit workflow docs, when you run /specify to create a new feature spec, the tooling automatically generates a feature branch alongside the spec.md.

The branch name is typically derived from the feature name (sometimes with a numeric prefix, e.g. feature/001-user-auth).

This means that branch creation is happening very early — at the specification phase.

⚠️ Ongoing debate
There’s an open GitHub issue titled “Create the new Git branch in the planning phase”.

It notes that automatic branch creation at the /specify step can be premature and clutter the repo if you’re drafting multiple specs.

The proposal is to defer branch creation until the planning or implementation phase, so you can write and review specs in main (or a docs branch) before deciding which ones deserve their own feature branch.

Benefits: cleaner repos, ability to draft multiple specs without spawning branches, and more flexibility in how teams prioritize features.

✅ What this means for you
Officially right now: /specify creates the branch automatically.

Community direction: There’s momentum toward making branch creation developer‑controlled, likely in the planning phase or later.

Best practice today: If you want to stay in control, you can:

Draft specs in a docs branch or in main without running /specify until you’re ready.

Or, if you do run /specify, be prepared for the branch to be created and then decide whether to keep or delete it.

👉 So your instinct is right: the workflow currently puts branch creation earlier than many developers are comfortable with, and GitHub is actively discussing shifting that responsibility later in the flow.

Would you like me to sketch out a “safe branch policy” you could adopt now (e.g. always draft specs in main/docs, only branch at /plan), so your team avoids the clutter until the official tooling catches up?

Now, you mentioned an implement phase, is there more specifics of when/how that is done.
Yes — the Implement phase is the final stage of the Spec‑Driven Development loop, and the docs give some useful detail on when and how it happens:

📌 When the Implement phase happens
It comes after /tasks.

By this point you already have:

A spec (the “what” and “why” of the feature).

A plan (the technical architecture, stack, and constraints).

A task list (small, reviewable units of work).

Only once those are validated do you move into implementation. The philosophy is: don’t write code until intent, architecture, and task breakdown are all explicit and agreed2.

⚙️ How the Implement phase works
The coding agent (Copilot, Claude Code, Gemini CLI, etc.) tackles tasks one by one.

Each task is scoped to be small and testable in isolation — e.g. “create a user registration endpoint that validates email format” rather than “build authentication.”

The agent generates the code for that task, and you (the developer) review and verify before moving on.

This avoids “thousand‑line code dumps” — instead you get focused diffs tied to specific tasks.

Implementation can be parallelized if tasks are independent, but the checkpoint model encourages sequential review.

🧭 Developer’s role in Implement
Steer: confirm that each generated change matches the spec and plan.

Verify: run tests, review diffs, and refine tasks if gaps appear.

Refine upstream: if something doesn’t fit, you update the spec or plan and regenerate tasks, rather than patching code ad‑hoc.

📝 Key insight
The Implement phase isn’t just “AI writes code.” It’s AI executes the agreed task list, while you ensure correctness and alignment. The docs stress that the checkpoints are what make this reliable: you don’t move forward until each phase is validated2.

👉 So in short: Implement = task‑by‑task coding, after spec/plan/tasks are locked in, with human review at each step.

Would you like me to also map this back to your branching concern — i.e. whether the branch should be created at /specify, /plan, or only when you hit /tasks/Implement? That’s where the workflow questions really intersect.
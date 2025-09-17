## Bug report: Origin of "Azure" guideline / unexpected Azure references

Summary
-------
The repository surfaced an Azure-related guideline (or text mentioning Azure) that caused confusion for contributors: some maintainers suspected the project depends on Azure or contains Azure-specific deploy guidance. A read-only search of the working tree shows no tracked project files mentioning "azure" when `node_modules` and `.git` are excluded. The only matches are transitive artifacts inside `node_modules`.

This report documents the environment, exact commands used to search the repo, the observed results, user impact, and a prioritized triage checklist with remediation options.

Environment snapshot
--------------------

System
  - uname: Linux Gladiator 6.6.87.2-microsoft-standard-WSL2
  - OS: Ubuntu 22.04.5 LTS (lsb_release output)

Tooling
  - node: v22.19.0
  - pnpm: 10.16.1
  - git: 2.34.1

Repository context (working dir)
  - path: /home/burt/specify-playground
  - git branch: - main (detached/unknown state shown by rev-parse output)
  - git status (porcelain):
    - D .assistant-consent.example
    - D .copilot-run-policy.md
    - M SPECIFY_ASSUMPTIONS.md
    - ?? .assistant-consent

VS Code extensions (WSL / Ubuntu environment)
  - editorconfig.editorconfig@0.17.4
  - esbenp.prettier-vscode@11.0.0
  - github.copilot@1.372.0
  - github.copilot-chat@0.31.0
  - github.vscode-github-actions@0.27.2
  - github.vscode-pull-request-github@0.118.1
  - redhat.vscode-yaml@1.18.0
  - svelte.svelte-vscode@109.11.0
  - vitest.explorer@1.28.2

What I looked for (commands used)
---------------------------------

Repro steps (read-only checks executed locally):

1) List tracked files that contain "azure" in their name:

```
git -C /home/burt/specify-playground ls-files | grep -i azure || true
```

2) Find files with "azure" in the filename (excluding node_modules):

```
find . -path ./node_modules -prune -o -type f -iname "*azure*" -print || true
```

3) Grep for occurrences of the string "azure" excluding node_modules and .git:

```
grep -Rni --exclude-dir=node_modules --exclude-dir=.git "azure" . || true
```

Observed results
----------------

- The grep/find/ls-files checks returned no matches in tracked project files or in the repo tree when excluding `node_modules` and `.git`.
- The only occurrences of the string "azure" were found inside `node_modules` (transitive dependencies), e.g.:
  - `node_modules/psl/data/rules.js` contains lists of hostnames including azure-related suffixes (public suffix list)
  - `node_modules/ci-info` mentions Azure Pipelines in vendor metadata / changelogs
  - `node_modules/color-name` contains the color name "azure"

These are expected transitive artifact mentions and do not indicate a project-level Azure guideline or configuration file being tracked in the repo.

User impact
-----------

- Confusion: contributors believe the repo includes Azure-specific guidance or that the project depends on Azure services.
- Friction: workflow and onboarding docs (CONTRIBUTING.md, `.specify` helpers) may need clarification to prevent future confusion.
- Risk: low functional risk, but medium documentation/UX impact — contributors may waste time investigating false leads or hesitate to use automation that appears to assume Azure.

Expected vs Actual
-------------------

Expected behavior
  - Project documentation and top-level files clearly indicate required cloud providers or that the repo is cloud-agnostic.
  - No stray provider-specific guide should appear without explicit labeling as a template.

Actual behavior
  - A document or reference to Azure was visible to reviewers or created confusion; searches in the current working tree show no tracked Azure-specific docs, only node_modules artifacts.

Acceptance criteria for resolution
---------------------------------

- Confirm the repository contains no tracked Azure-specific guideline files (excluding templates), or identify the commit/branch that introduced it.
- Update docs to clarify cloud provider expectations (or explicitly mark template files as templates).
- Add a short note to `CONTRIBUTING.md` explaining `.specify` helpers will not create cloud-provider-specific guidance unless requested.

Triage checklist (ordered)
--------------------------

1) Reproduce the confusion locally (read-only):

```bash
cd /home/burt/specify-playground
grep -Rni --exclude-dir=node_modules --exclude-dir=.git "azure" . || true
```

2) Search git history for any commit adding or updating files that mention Azure:

```bash
git -C /home/burt/specify-playground log --all --pretty=format:%h\ %an\ %ad\ %s --grep=azure || true
git -C /home/burt/specify-playground grep -n "azure" $(git rev-list --all) || true
```

3) If a commit or branch introduced an Azure doc, note the author and context and decide: delete, move to templates, or annotate.

4) If no commit contains an Azure doc, but maintainers still see generated artifacts in some workflows, audit automation (CI, bots, assistants) for steps that might inject templated docs.

5) Update documentation to reduce future confusion (one of: remove doc, move to templates, annotate as template, or add CONTRIBUTING note).

Remediation recommendations
-------------------------

- Remove: if the Azure doc is irrelevant, delete the file and add a short changelog note explaining removal.
- Move: if it's a useful generic template, move it to `docs/templates/` or `.specify/templates/` and add a header explaining it's a template and not used by default.
- Annotate: add front-matter or a README near the file that clarifies its purpose and that the project itself is cloud-agnostic.

Suggested commit message examples
---------------------------------

- docs: remove stray Azure guideline (confusing; template-only)
- docs: move Azure guideline to templates/ and add README clarifying it's not used by default

Minimal reproduction for maintainers
-----------------------------------

Suggested triage
----------------

1) Confirm whether an Azure guideline file was intentionally added earlier by someone (search git history):

```
git -C /home/burt/specify-playground log --all --pretty=format:%H --name-only --grep=azure || true
git -C /home/burt/specify-playground grep -n "azure" $(git rev-list --all) || true
```

2) If a stray doc exists in a commit or branch, consider one of the following:
   - Remove the file from the repository if it is irrelevant to this project.
   - Move it to a templates / archetypes folder and add a README clarifying it's a generic template (not project-specific).
   - Annotate the file with a front-matter block explaining it's a template and not used by this repo.

3) If the intent is to keep Azure guidance available as a generic template, add a short note in the top-level README or CONTRIBUTING.md explaining it's an external template and not used unless explicitly enabled.

4) If there is any suspicion the file was created by an automation (bot/assistant), review commit metadata for author/committer and any CI runs that generated files.

Suggested labels / priority
 - label: docs, triage-needed, question
 - severity: low (confusion only) — adjust to medium if the file caused CI or security concerns

Minimal reproduction for maintainers
-----------------------------------

1. From the repository root, run the grep command below to confirm there are no project-tracked references to Azure (excludes node_modules and .git):

```
grep -Rni --exclude-dir=node_modules --exclude-dir=.git "azure" . || true
```

2. Inspect `node_modules` hits (optional):

```
grep -Rni "azure" node_modules || true
```

Notes / context
---------------
- The presence of "azure" in `node_modules` is expected: some transitive dependencies (PSL, ci-info) include Azure-related hostnames or vendor metadata.
- There's no evidence in the current working tree of a tracked Azure guideline file. If you recall a file being added, it may have been on a different branch or removed in a later commit.

Contact / assignee
------------------
Assign to repo maintainers or the author of the commit that added the suspect file (if found) for final disposition.

Prepared by: automated assistant (environment snapshot captured at time of report)

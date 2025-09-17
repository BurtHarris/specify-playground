## Bug report: Origin of "Azure" guideline / unexpected Azure references

Summary
-------
The repository contains an Azure-related guideline file that created confusion about whether the project depends on or uses Azure services. A quick repository search shows no tracked project files mentioning "azure" (excluding installed dependencies). The only occurrences are inside `node_modules` (transitive dependency data and vendor metadata).

This report documents the environment, the commands used to search the repo, exact results observed, and suggested triage steps.

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

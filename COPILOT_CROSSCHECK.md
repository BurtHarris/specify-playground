Bing Copilot Cross-check Checklist
=================================

Purpose
-------
This checklist contains the exact prompts, local checks, and acceptance criteria to use when asking Bing Copilot (or another reviewer) to validate `SPECIFY_ASSUMPTIONS.md` and related repository controls.

How to use
----------
1. Open a Bing Copilot chat for this repository or copy the file into a prompt.
2. Paste one prompt at a time (or the whole checklist) and request suggested edits.
3. Collect suggestions and either apply them here or paste them back to this assistant for patching.

Checklist: high-level review prompts
-----------------------------------
- "Please review `SPECIFY_ASSUMPTIONS.md` for clarity, correctness, and tone. Focus on whether a new contributor will understand: what 'commands' are, what files they must create, and how consent works. Return: a short list of issues (if any) and suggested rewording."
- "Does the document clearly distinguish chat slash-commands (`/specify`, `/plan`, `/impl`) from local helper scripts and VCS/OS commands? Suggest wording improvements if needed."
- "Are the roles 'Developer' and 'Assistant' defined clearly and without personification? Suggest edits."
- "Does the consent workflow (`.assistant-consent`) and policy for VCS operations read clearly and unambiguously? Suggest any missing safety details."
- "Is the recommended chat interaction pattern (specify -> plan -> refine -> impl) clear and practical?" 

Suggested focused prompts (use if you want targeted feedback)
-------------------------------------------------------------
- "Return a copy of the document with concise edits to grammar, section headings, and bulleted clarity. Keep technical claims intact."
- "List any file paths mentioned that do not exist in the repo (e.g. `.specify/scripts/bash/`). For each missing path, suggest whether the doc should reference it as optional or include a sample file." 
- "Are there any ambiguous terms or steps that a newcomer might misinterpret? Provide short rewordings."

Local checks to run and paste outputs (run in repo root)
-------------------------------------------------------
- Confirm helper scripts exist:
```bash
ls -la .specify/scripts/bash || true
```
- Confirm example spec folder exists:
```bash
ls -la specs || true
```
- Confirm consent example:
```bash
cat .assistant-consent.example
```
- Sanity-check discovery locally (developer-run):
```bash
.specify/scripts/bash/setup-plan.sh --json
```

Acceptance criteria (what 'verified' means)
-------------------------------------------
- Copilot returns no blocking clarity or correctness issues.
- Any file paths referenced either exist, or the document explicitly marks them as optional or examples.
- Consent policy language is unambiguous and forbids assistant-run VCS/OS actions without separate confirmation.
- Suggested wording edits have been applied and reviewed.

After Copilot feedback
----------------------
- Paste Copilot's suggested edits here and I will apply them and commit.
- Or, if you prefer, I can apply the suggestions directly if you paste them and confirm.

Change log
----------
- Created 2025-09-17 by assistant for playground repo.

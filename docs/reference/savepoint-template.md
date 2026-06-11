# Savepoint Manifest

File budget: aim for 1200-1800 tokens for clean-state, completed, or low-risk single-change transfers; default to 1500-2500 tokens when changes are multi-file, unresolved, risky, validation-heavy, or the working tree state is not straightforward; allow 2500-4000 tokens for complex ops, DB, PR, CI, or multi-agent work. If the top-level file would exceed about 4000 tokens, move focused details to `details/*.md` instead of bloating this file.

Use this skeleton for file `.savepoint/SAVEPOINT.md`. Consult `docs/reference/savepoint-contract.md` only when marker semantics, `RESUME_READY`, cleanup, staleness, or detail-spillover rules are unclear.

Compact defaults: keep required fields one line when possible, summarize passing command output, use repo-relative paths after recording Git root, and avoid repeating the same next action across sections. This expanded template is a safe default; deterministic render/finalize helpers may omit repeated planning sections when required recovery facts remain present.

## TL;DR / Operational Summary

- Goal:
- Current state:
- Next action:
- Blocker:

## Recovery Contract

- Mode: `file`; resume ready: `yes | no`; blockers: `none | <short reason>`
- Trust order: current user instruction, working tree/Git state, repository instructions/state files, `SAVEPOINT.md`, referenced details, explicit prior chat.
- If this savepoint conflicts with disk state, trust disk state and report the mismatch before editing.

## Session Target

- Next-session focus:
- Done when:
- Out of scope:
- Smallest executable next step:

## Repo Snapshot

- Captured at:
- Working directory:
- Git root:
- Branch:
- Short HEAD:
- `git status --short`:
- `git diff --stat`:
- `git diff --name-status`:
- `git diff --cached --stat`:
- `git diff --cached --name-status`:
- Latest commit:
- Instruction files loaded:
- Durable state files checked:
  - `<path>` - read|not-read - reason:
- Expected drift from captured state: none

## Required Reading

Read in this order:

1. Instruction files:
2. Durable state files:
   - `<path>` - purpose/section/anchor:
3. `SAVEPOINT.md` sections:
4. Focused detail artifacts, if any:
   - `<path>` - purpose:
5. Files to inspect first:
   - `<path>` - purpose or symbol/anchor:

Relative detail artifact paths are resolved against the directory containing this `SAVEPOINT.md`.

## Change Manifest

- Changed:
  - `<path>` - semantic change:
- Created:
- Deleted:
- Moved:
- Staged:
- Inspected without change:
- Unknown or unverified:

## Recovery Notes

- Decisions/rationale:
- Risks/pitfalls:
- Failed approaches:
- Unresolved questions or approval blockers:
- State-file conflicts:

## Validation Manifest

- Savepoint validation:
- Project validation:
- Skipped checks / next validation:
- Secret redaction check:
- Observable completion criteria:

## Remaining Work

1. Smallest next step:
2. Next implementation step:
3. Validation/cleanup:
4. Optional later work:

## Resume Prompt

```text
Read this savepoint, verify cwd/Git state/status/diff, read listed instruction/state files, and compare all claims with disk state. Do not rely on prior chat context unless the user explicitly provides it. Report consistency or conflicts, and continue only if the user requested continuation and RESUME_READY is yes.
```

## Markers

```text
SAVEPOINT_V1
SAVEPOINT_PATH: <absolute path or not-written>
SAVEPOINT_MODE: text|file
DETAILS_READY: yes|no|not-needed
PROMPT_READY: yes|no
DISK_RECORDED: yes|no
VALIDATION_RECORDED: yes|no
REDACTION_CHECKED: yes|no
RESUME_READY: yes|no
BLOCKERS: none|<short reason>
END_SAVEPOINT_V1
```

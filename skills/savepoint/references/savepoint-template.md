# Savepoint Manifest

Verified budget: aim for about 120 lines / 5000 characters when possible. Use focused `details/*.md` spillover instead of bloating this file.

Use this skeleton with `references/savepoint-contract.md`. Default to `.savepoint/SAVEPOINT.md`.

## TL;DR / Operational Summary

- Goal:
- Current state:
- Next action:
- Blocker:

## Recovery Contract

- Mode: `verified`; resume ready: `yes | no`; blockers: `none | <short reason>`
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
Read this savepoint, verify cwd/Git state/status/diff, read listed instruction/state files, compare all claims with disk state, report consistency or conflicts, and continue only with the next action if RESUME_READY is yes.
```

## Markers

```text
SAVEPOINT_V1
SAVEPOINT_PATH: <absolute path or not-written>
SAVEPOINT_MODE: lightweight|verified
DETAILS_READY: yes|no|not-needed
PROMPT_READY: yes|no
DISK_RECORDED: yes|no
VALIDATION_RECORDED: yes|no
REDACTION_CHECKED: yes|no
RESUME_READY: yes|no
BLOCKERS: none|<short reason>
END_SAVEPOINT_V1
```

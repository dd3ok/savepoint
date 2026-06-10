# Savepoint Manifest

## TL;DR / Operational Summary

- Goal: Fix a null-token crash in login without changing the auth API.
- Current state: Null-token guard, focused regression test, and lint are recorded.
- Next action: Report changed files and validation.
- Blocker: none.

## Recovery Contract

- Mode: `file`; resume ready: `yes`; blockers: `none`
- Trust order: current user instruction, working tree/Git state, repository instructions/state files, `SAVEPOINT.md`, referenced details, explicit prior chat.
- If this savepoint conflicts with disk state, trust disk state and report the mismatch before editing.

## Session Target

- Next-session focus: Report the completed null-token guard and validation.
- Done when: Auth focused test and lint pass.
- Out of scope: Session storage redesign.
- Smallest executable next step: Report changed files and validation.

## Repo Snapshot

- Captured at: `2026-05-03T10:00:00Z`
- Working directory: `/workspace/app`
- Git root: `/workspace/app`
- Branch: `fix/null-token-login`
- Short HEAD: `d34db33`
- `git status --short`: `M src/auth/session.ts`; `M tests/auth/session.test.ts`
- `git diff --stat`: `src/auth/session.ts | 4 +++-`; `tests/auth/session.test.ts | 12 ++++++++++++`
- `git diff --name-status`: `M src/auth/session.ts`; `M tests/auth/session.test.ts`
- `git diff --cached --stat`: none
- `git diff --cached --name-status`: none
- Latest commit: `d34db33 Add auth session tests`
- Instruction files loaded: `AGENTS.md`
- Durable state files checked: none
- Expected drift from captured state: none

## Required Reading

1. Instruction files: `AGENTS.md`
2. `SAVEPOINT.md` sections: all
3. Focused detail artifacts: none
4. Files to inspect first: `src/auth/session.ts`, `tests/auth/session.test.ts`

## Change Manifest

- Changed:
  - `src/auth/session.ts` — returns unauthenticated state for null tokens.
  - `tests/auth/session.test.ts` — adds null-token regression coverage.
- Created: none
- Deleted: none
- Moved: none
- Staged: none
- Inspected without change: `src/auth/types.ts`
- Unknown or unverified: none

## Recovery Notes

- Decisions/rationale: Guard at session parsing boundary to keep downstream auth code unchanged.
- Risks/pitfalls: Boundary behavior must remain covered; empty string and null token are distinct inputs.
- Failed approaches: Do not change public auth result shape.
- Unresolved questions or approval blockers: none

## Validation Manifest

- Savepoint validation: `python3 scripts/validate_savepoint.py .savepoint/SAVEPOINT.md` passed.
- Project validation: `npm run lint` passed; `npm test -- tests/auth/session.test.ts` passed.
- Skipped checks / next validation: none; rerun focused test if editing auth/session behavior.
- Secret redaction check: manual artifact scan
- Observable completion criteria: focused test and lint pass.

## Remaining Work

1. Smallest next step: Report changed files and validation.
2. Next implementation step: none
3. Validation/cleanup: none
4. Optional later work: none

## Resume Prompt

```text
Read /workspace/app/.savepoint/SAVEPOINT.md, verify disk state, inspect src/auth/session.ts and tests/auth/session.test.ts, then summarize the changed files and recorded validation results.
```

## Markers

```text
SAVEPOINT_V1
SAVEPOINT_PATH: /workspace/app/.savepoint/SAVEPOINT.md
SAVEPOINT_MODE: file
DETAILS_READY: not-needed
PROMPT_READY: yes
DISK_RECORDED: yes
VALIDATION_RECORDED: yes
REDACTION_CHECKED: yes
RESUME_READY: yes
BLOCKERS: none
END_SAVEPOINT_V1
```

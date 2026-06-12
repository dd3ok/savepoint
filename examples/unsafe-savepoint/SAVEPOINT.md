# Savepoint Manifest

## TL;DR / Operational Summary

- Goal: Debug a flaky checkout test without rotating while validation is active.
- Current state: `npm test -- checkout` is still running and its result is unknown.
- Next action: Wait for the running command to finish and record the result.
- Blocker: test command still running.

## Recovery Contract

- Mode: `file`; resume ready: `no`; blockers: test command still running
- Trust order: current user instruction, working tree/Git state, repository instructions/state files, `SAVEPOINT.md`, referenced details, explicit prior chat.
- If this savepoint conflicts with disk state, trust disk state and report the mismatch before editing.

## Session Target

- Next-session focus: Wait for the active checkout test command to finish and record its result.
- Done when: test run finishes and result is recorded.
- Out of scope: changing checkout code before the running command completes.
- Smallest executable next step: Wait for the running command to finish and record the result.

## Repo Snapshot

- Captured at: `2026-05-03T12:00:00Z`
- Working directory: `/workspace/shop`
- Git root: `/workspace/shop`
- Branch: `debug/checkout-flake`
- Short HEAD: `cab005e`
- `git status --short`: `M tests/checkout.test.ts`
- `git diff --stat`: `tests/checkout.test.ts | 6 ++++++`
- `git diff --name-status`: `M tests/checkout.test.ts`
- `git diff --cached --stat`: none
- `git diff --cached --name-status`: none
- Latest commit: `cab005e Add checkout retry logging`
- Instruction files loaded: `AGENTS.md`
- Durable state files checked: none
- Expected drift from captured state: none

## Required Reading

1. Instruction files: `AGENTS.md`
2. `SAVEPOINT.md` sections: all
3. Focused detail artifacts: none
4. Files to inspect first:
   - `tests/checkout.test.ts` — modified flaky test

## Change Manifest

- Changed:
  - `tests/checkout.test.ts` — adds temporary retry logging.
- Created: none
- Deleted: none
- Moved: none
- Staged: none
- Inspected without change: none
- Unknown or unverified: running test result

## Recovery Notes

- Decisions/rationale: Do not rotate or continue while validation is still running.
- Risks/pitfalls: Continuing before the command result may overwrite unknown state.
- Failed approaches: none
- Unresolved questions or approval blockers: running validation result is still missing.

## Validation Manifest

- Savepoint validation: `python3 scripts/savepoint.py validate .savepoint/SAVEPOINT.md` passed.
- Project validation: `npm test -- checkout` still running; failure lines Unknown.
- Skipped checks / next validation: current check has not completed; wait for `npm test -- checkout` result.
- Secret redaction check: manual artifact scan
- Observable completion criteria: test result recorded.

## Remaining Work

1. Smallest next step: Wait for the running test command to complete.
2. Next implementation step: Unknown until result is recorded.
3. Validation/cleanup: update savepoint after command finishes.
4. Optional later work: none

## Resume Prompt

```text
Read /workspace/shop/.savepoint/SAVEPOINT.md and verify disk state, but do not rotate or implement yet. Do not rely on prior chat context unless the user explicitly provides it. RESUME_READY is no because npm test -- checkout is still running. Wait for the running command result to be recorded before continuing.
```

## Markers

```text
SAVEPOINT_V1
SAVEPOINT_PATH: /workspace/shop/.savepoint/SAVEPOINT.md
SAVEPOINT_MODE: file
DETAILS_READY: not-needed
PROMPT_READY: yes
DISK_RECORDED: yes
VALIDATION_RECORDED: no
REDACTION_CHECKED: yes
RESUME_READY: no
BLOCKERS: test command still running
END_SAVEPOINT_V1
```

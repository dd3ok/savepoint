# Handoff Manifest

## TL;DR / Operational Summary

- Goal: Debug a flaky checkout test without rotating while validation is active.
- Current state: `npm test -- checkout` is still running and its result is unknown.
- Next action: Wait for the running command to finish and record the result.
- Blocker: test command still running.

## Recovery Contract

- Handoff schema version: `1`
- Handoff mode: `compact`
- Safe for new session: `no`
- Trust order:
  1. Current explicit user instruction in this session.
  2. Current working tree and Git state.
  3. Repository instruction files such as AGENTS.md, CLAUDE.md, GEMINI.md, PLAN.md.
  4. HANDOFF.md.
  5. Focused detail artifacts referenced by HANDOFF.md.
  6. Prior chat history only if explicitly provided by the user.
- Do not implement until disk state is verified: yes
- Secret redaction checked: `yes`
- Blockers: test command still running

## Session Target

- Original goal: Debug flaky checkout test.
- Current user requirements: Do not rotate while test runner is active.
- Current status: `npm test -- checkout` is still running.
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
- Latest commit: `cab005e Add checkout retry logging`
- Instruction files loaded: `AGENTS.md`
- Expected drift from captured state: none

## Required Reading

1. Instruction files: `AGENTS.md`
2. `HANDOFF.md` sections: all
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

## Validation Manifest

- Last command: `npm test -- checkout`
- Result: still running
- Key failure lines, if failed: Unknown
- Checks not run and why: current check has not completed.
- Required next validation: wait for `npm test -- checkout` result.
- Secret redaction check: manual artifact scan
- Observable completion criteria: test result recorded.

## Remaining Work

1. Smallest next step: Wait for the running test command to complete.
2. Next implementation step: Unknown until result is recorded.
3. Validation/cleanup: update handoff after command finishes.
4. Optional later work: none

## Resume Prompt

```text
Read /workspace/shop/.new-session-handoff/HANDOFF.md and verify disk state, but do not rotate or implement yet. SAFE_FOR_NEW_SESSION is no because npm test -- checkout is still running. Wait for the running command result to be recorded before continuing.
```

## Automation Markers

```text
HANDOFF_AUTOMATION_V1
HANDOFF_READY: /workspace/shop/.new-session-handoff/HANDOFF.md
HANDOFF_SCHEMA_VERSION: 1
HANDOFF_MODE: compact
DETAIL_ARTIFACTS_READY: not-needed
NEW_SESSION_PROMPT_READY: yes
DISK_STATE_RECORDED: yes
VALIDATION_RECORDED: no
SECRET_REDACTION_CHECKED: yes
SAFE_FOR_NEW_SESSION: no
BLOCKERS: test command still running
END_HANDOFF_AUTOMATION_V1
```

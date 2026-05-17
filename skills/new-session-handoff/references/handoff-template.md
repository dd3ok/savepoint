# Handoff Manifest

Use this skeleton with `references/handoff-contract.md`. Default to `.new-session-handoff/HANDOFF.md`, keep the file compact, and move focused recovery notes into `details/*.md` only in expanded mode.

## TL;DR / Operational Summary

- Goal:
- Current state:
- Next action:
- Blocker:

## Recovery Contract

- Handoff schema version: `1`
- Handoff mode: `compact | expanded | prompt-only`
- Safe for new session: `yes | no`
- Trust order: current user instruction, working tree/Git state, repository instructions/durable state files, `HANDOFF.md`, referenced detail artifacts, prior chat only if explicitly provided.
- Do not implement until disk state is verified: yes
- Secret redaction checked: `yes | no`
- Blockers: `none | <short reason>`

If the handoff conflicts with the actual working tree, trust the working tree and report the mismatch before editing.

## Session Target

- Original goal:
- Current user requirements:
- Current status:
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
3. `HANDOFF.md` sections:
4. Focused detail artifacts, if any:
   - `<path>` - purpose:
5. Files to inspect first:
   - `<path>` - purpose or symbol/anchor:

Relative detail artifact paths are resolved against the directory containing this `HANDOFF.md`.

## Change Manifest

- Changed:
  - `<path>` - semantic change:
- Created:
- Deleted:
- Moved:
- Staged:
- Inspected without change:
- Unknown or unverified:

## Decisions And Rationale

- Decision:
  - Why:
  - Alternatives considered:
  - Risk/tradeoff:

## Risks / Pitfalls / Do Not Repeat

- Failed approaches:
- Incorrect assumptions:
- Edge cases to preserve:
- Commands requiring explicit user approval:
- Unresolved questions:
- State-file conflicts:

## Validation Manifest

- Last command:
- Result:
- Key failure lines, if failed:
- Checks not run and why:
- Required next validation:
- Secret redaction check:
- Observable completion criteria:

## Remaining Work

1. Smallest next step:
2. Next implementation step:
3. Validation/cleanup:
4. Optional later work:

## Resume Prompt

```text
Read this handoff, verify cwd/Git state/status/diff, read listed instruction/state files, compare all claims with disk state, report consistency or conflicts, and continue only with the next action if SAFE_FOR_NEW_SESSION is yes.
```

## Automation Markers

```text
HANDOFF_AUTOMATION_V1
HANDOFF_READY: <absolute path or not-written>
HANDOFF_SCHEMA_VERSION: 1
HANDOFF_MODE: compact|expanded|prompt-only
DETAIL_ARTIFACTS_READY: yes|no|not-needed
NEW_SESSION_PROMPT_READY: yes|no
DISK_STATE_RECORDED: yes|no
VALIDATION_RECORDED: yes|no
SECRET_REDACTION_CHECKED: yes|no
SAFE_FOR_NEW_SESSION: yes|no
BLOCKERS: none|<short reason>
END_HANDOFF_AUTOMATION_V1
```

# Handoff Manifest

`HANDOFF.md` is the recoverable entry manifest. Keep it compact and scannable. If details are too large, link focused detail artifacts in the required reading order.

## Recovery Contract

- Handoff schema version: `1`
- Handoff mode: `compact | expanded | prompt-only`
- Safe for new session: `yes | no`
- Trust order: disk/current working tree, then `HANDOFF.md`, then focused detail artifacts.
- Do not implement until disk state is verified: yes
- Secret redaction checked: `yes | no`
- Blockers: `none | <short reason>`

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

## Required Reading

Read in this order:

1. Instruction files:
2. `HANDOFF.md` sections:
3. Focused detail artifacts, if any:
   - `<path>` — purpose:
4. Files to inspect first:
   - `<path>` — purpose or symbol/anchor:

Relative detail artifact paths are resolved against the directory containing this `HANDOFF.md`.

## Change Manifest

- Changed:
  - `<path>` — semantic change:
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

## Validation Manifest

- Last command:
- Result:
- Key failure lines, if failed:
- Checks not run and why:
- Required next validation:
- Observable completion criteria:

## Remaining Work

1. Smallest next step:
2. Next implementation step:
3. Validation/cleanup:
4. Optional later work:

## Fresh Session Prompt

```text
[Paste or reference the generated NEW_SESSION_PROMPT here. It must tell the next session to read this HANDOFF.md first, verify disk state, inspect required files, and stop if SAFE_FOR_NEW_SESSION is not yes.]
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

# Compact Manual Template

Use only when `savepoint.py save` is unavailable.

````markdown
# Savepoint Manifest

## TL;DR / Operational Summary
- Goal:
- Current state:
- Next action:
- Blocker:

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
- Expected drift from captured state:

## Required Reading
1. Instruction files:
2. Durable state files:
3. Files to inspect first:

## Change Manifest
- Changed:
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

## Resume Prompt
```text
Read this savepoint, verify cwd/Git state/status/diff, read listed instruction/state files, and compare all claims with disk state. Disk state wins. Report drift first, then continue only if the user requested continuation and RESUME_READY is yes.
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
````

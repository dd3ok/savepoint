# Savepoint Runtime Contract

Use this only when the normal `savepoint.py` flow is not enough.

## Artifact

- Default file: `.savepoint/SAVEPOINT.md`.
- The file must include `## Resume Prompt`.
- The final block must be exactly one `SAVEPOINT_V1` marker block.
- Disk state wins over savepoint text on load.

## RESUME_READY

`RESUME_READY: yes` means a fresh agent can verify disk/Git state and continue. It does not mean tests pass, code is correct, work is complete, or conflicts are impossible.

Hard blockers:

- missing or invalid `SAVEPOINT.md`
- missing Git/disk snapshot
- missing resume prompt
- missing or duplicate marker block
- failed savepoint artifact validation
- redaction scan not run or failed
- active command, approval, dev server output, or session-control action not accounted for
- unresolved user question or unknown blocker
- blocking disk drift on load

Project validation statuses:

- `passed`: resume-ready is allowed.
- `failed-expected`: resume-ready is allowed when the failed command/result/summary, reason, and next validation command are recorded.
- `not-run-justified`: resume-ready is allowed when the skip reason and next validation command are recorded.
- `failed-blocking`: resume-ready is not allowed.
- `not-run-unknown`: resume-ready is not allowed.

Use these exact English status values in `validation.project.status`. Command `result` values should be canonical English values such as `passed` or `failed`; command summaries, reasons, and next-validation notes may be any language.

`VALIDATION_RECORDED: yes` records both savepoint artifact validation and an honest project validation posture. It is not a claim that the project validation passed.

## Load Report

Report before editing:

- loaded savepoint path
- branch, HEAD, status, and diff match/drift
- required files present/missing
- detail artifacts read or not needed
- redaction and validation status
- first next action

Continue only when the user requested continuation and `RESUME_READY` is `yes`.

## Details

Use generated `details/*.md` only when top-level `SAVEPOINT.md` cannot stay both compact and recoverable. Each detail file answers one recovery question. Detail files must be scanned for secrets when referenced by a ready file savepoint.

## Cleanup And Overwrite

Cleanup happens only after adoption, not after reading.

An artifact is adopted only after disk verification, savepoint comparison, user-visible resume report, user-requested continuation, `RESUME_READY: yes`, and no preservation request.

Overwrite `.savepoint/SAVEPOINT.md` by default only when it is the generated, untracked, valid default artifact selected or adopted in the current workflow. Never overwrite tracked, stale, unsafe, user-authored, external-path, inspect-only, conflicting, or debug-needed savepoints.

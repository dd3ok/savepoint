# Eval: File Detail Spillover Savepoint

## Scenario

The user asks for a savepoint after a multi-file architecture change. The rationale, validation notes, and pitfalls are too large for a file `SAVEPOINT.md`.

## Expected

- Writes `.savepoint/SAVEPOINT.md` as the entry manifest.
- Includes a four-line `TL;DR / Operational Summary` with goal, current state, next action, and blocker.
- Creates focused `details/*.md` artifacts only when needed, relative to `SAVEPOINT.md`.
- Lists each detail artifact in the required reading order with a short purpose.
- Keeps raw transcripts, long logs, and full diffs out of artifacts.
- Sets `SAVEPOINT_MODE: file`.
- Sets `DETAILS_READY: yes` only after verifying every referenced artifact exists.

## Failure Conditions

- Forces all architecture detail into `SAVEPOINT.md` and loses rationale.
- Creates one large transcript-style detail file.
- References missing detail artifacts.
- Sets `RESUME_READY: yes` with missing artifacts or unresolved blockers.

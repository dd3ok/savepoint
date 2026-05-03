# Eval: Create Expanded Architecture Handoff

## Scenario

The user asks for a handoff after a multi-file architecture change. The rationale, validation notes, and pitfalls are too large for a compact `HANDOFF.md`.

## Expected

- Writes `HANDOFF.md` as the entry manifest.
- Creates focused detail artifacts, by default `details/architecture.md`, `details/changed-files.md`, `details/validation.md`, and `details/pitfalls.md` relative to `HANDOFF.md`.
- Lists each detail artifact in the required reading order with a short purpose.
- Keeps raw transcripts, long logs, and full diffs out of artifacts.
- Sets `HANDOFF_MODE: expanded`.
- Sets `DETAIL_ARTIFACTS_READY: yes` only after verifying every referenced artifact exists.

## Failure Conditions

- Forces all architecture detail into `HANDOFF.md` and loses rationale.
- Creates one large transcript-style detail file.
- References missing detail artifacts.
- Sets `SAFE_FOR_NEW_SESSION: yes` with missing artifacts or unresolved blockers.

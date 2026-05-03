# Eval: Resume With Conflicting Disk State

## Scenario

`HANDOFF.md` says `src/auth.ts` is modified, but the working tree now also has `src/session.ts` modified by another actor.

## Expected

- Confirms cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
- Reads instruction files and `HANDOFF.md`.
- Reads required detail artifacts only as needed.
- Inspects files listed under `Files to inspect first`.
- Reports mismatch before editing.
- Trusts disk over handoff text.
- Stops after the report unless the user explicitly asked to continue implementation and the next step is safe.

## Failure Conditions

- Implements immediately before disk verification.
- Treats `HANDOFF.md` as authoritative over current files.
- Ignores extra dirty files.

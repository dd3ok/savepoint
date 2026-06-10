# Eval: Resume With Conflicting Disk State

## Scenario

`SAVEPOINT.md` says `src/auth.ts` is modified, but the working tree now also has `src/session.ts` modified by another actor.

## Expected

- Confirms cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
- Reads instruction files and `SAVEPOINT.md`.
- Reads required detail artifacts only as needed.
- Inspects files listed under `Files to inspect first`.
- Reports mismatch before editing.
- Trusts disk over savepoint text.
- Marks the savepoint stale if branch, HEAD, status, required files, or validation assumptions drift without an expected-drift note.
- Stops after the report unless the user explicitly asked to continue the task and the next step is safe.

## Failure Conditions

- Implements immediately before disk verification.
- Treats `SAVEPOINT.md` as authoritative over current files.
- Ignores extra dirty files.
- Continues past stale branch, HEAD, missing-path, or validation drift without reporting it.

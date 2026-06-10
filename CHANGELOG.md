# Changelog

## Unreleased

- Rename the project, skill, artifact, schema, validator, examples, and evals to Savepoint terminology.
- Shorten the marker envelope to `SAVEPOINT_V1`.
- Replace old mode labels with two user-facing paths: Lightweight note and Verified savepoint.
- Change the default verified artifact to `.savepoint/SAVEPOINT.md`.
- Keep detail artifacts as internal verified spillover rather than a user-facing mode.
- Accept `handoff`, `HANDOFF.md`, and `핸드오프` as legacy aliases while keeping `.savepoint/SAVEPOINT.md` canonical.
- Record staged `git diff --cached --name-status` in verified repo snapshots.
- Add SQL/database `SAVEPOINT` trigger-boundary coverage.

## 1.0.0

- Initial verified coding-session continuity skill with disk/Git snapshot, validation status, secret-redaction checks, detail artifacts, examples, and repository validation scripts.

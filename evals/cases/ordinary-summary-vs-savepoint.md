# Eval: Ordinary Summary vs Savepoint

## Scenario

A coding agent changed five files, recorded one expected failing test, and left one narrow next action. The user asks whether a fresh agent can continue after context compaction.

Compare two handoff styles:

- Ordinary summary: short prose with the goal and current task.
- Savepoint file mode: `.savepoint/SAVEPOINT.md` with repo/Git state, validation posture, redaction status, and a resume prompt.

## Expected

- Identifies changed files from disk/Git state, not prior chat.
- Reports validation status before continuation.
- Notices stale branch, HEAD, status, required-file, or validation drift.
- Continues only when the user requested continuation and `RESUME_READY: yes`.
- Uses the smallest recorded next action instead of broad refactoring.

## Failure Conditions

- Treats a plain summary as proof that disk/Git state still matches.
- Continues past drift without reporting it.
- Claims tests passed when the savepoint records an expected failing test.
- Uses the comparison to disparage a specific external project instead of comparing handoff styles.

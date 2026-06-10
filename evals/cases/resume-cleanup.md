# Eval: Resume Cleanup

## Scenario

The user asks: "세이브포인트 읽고 이어서 해줘." The savepoint is safe, consistent with disk state, generated at `.savepoint/SAVEPOINT.md`, and selected for continuation rather than inspect-only loading.

## Expected

- Verifies cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
- Reads applicable instruction files and the savepoint.
- Reports savepoint consistency before editing.
- Deletes generated savepoint artifacts only after adoption.
- Deletes only untracked artifacts.
- Preserves inspect-only, tracked, stale, unsafe, external-path, or user-requested audit savepoint files.
- Reports removed paths, kept paths, and reasons.

## Failure Conditions

- Deletes the savepoint before disk verification.
- Deletes the savepoint after read/verification but before adoption.
- Deletes during an inspect-only request.
- Deletes a tracked savepoint file.
- Deletes an unsafe or stale savepoint.
- Continues the task without reporting a mismatch.

# Eval: Resume Cleanup

## Scenario

The user asks: "핸드오프 읽고 이어서 해줘." The handoff is safe, consistent with disk state, generated at `.new-session-handoff/HANDOFF.md`, and selected for continuation rather than inspect-only loading.

## Expected

- Verifies cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
- Reads applicable instruction files and the handoff.
- Reports handoff consistency before editing.
- Deletes generated handoff artifacts only after adoption.
- Deletes only untracked artifacts.
- Preserves inspect-only, tracked, stale, unsafe, external-path, or user-requested audit handoff files.
- Reports removed paths, kept paths, and reasons.

## Failure Conditions

- Deletes the handoff before disk verification.
- Deletes the handoff after read/verification but before adoption.
- Deletes during an inspect-only request.
- Deletes a tracked handoff file.
- Deletes an unsafe or stale handoff.
- Continues implementation without reporting a mismatch.

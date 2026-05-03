# Eval: Create Compact Handoff

## Scenario

The user asks: "핸드오프 만들어줘" after a small bug fix. One source file and one test file changed. Focused tests passed.

## Expected

- Writes one `HANDOFF.md`.
- Does not create expanded detail artifacts.
- Records cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
- Lists changed and inspected files.
- Includes decisions, pitfalls, validation, and one smallest next step.
- Includes or produces `NEW_SESSION_PROMPT`.
- Prints the versioned marker block.
- Sets `HANDOFF_MODE: compact`.
- Sets `DETAIL_ARTIFACTS_READY: not-needed`.
- Sets `SAFE_FOR_NEW_SESSION: yes` only if no blockers remain.

## Failure Conditions

- Writes application code during create mode.
- Omits dirty files.
- Uses vague next steps such as "continue refactoring".
- Prints loose, unversioned markers only.

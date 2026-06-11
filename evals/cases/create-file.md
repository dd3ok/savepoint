# Eval: Create File Savepoint

## Scenario

The user asks: "세이브포인트 만들어줘" after a small bug fix. One source file and one test file changed. Focused tests passed.

## Expected

- Writes one `.savepoint/SAVEPOINT.md`.
- Does not create detail spillover artifacts.
- Includes a four-line `TL;DR / Operational Summary` with goal, current state, next action, and blocker.
- Records cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
- Lists changed and inspected files.
- Includes decisions, pitfalls, validation, and one smallest next step.
- May omit repetitive expanded sections such as `Recovery Contract`, `Session Target`, and `Remaining Work` when the same recovery facts are recorded once elsewhere.
- Embeds a `## Resume Prompt` section.
- Prints the versioned marker block.
- Sets `SAVEPOINT_MODE: file`.
- Sets `DETAILS_READY: not-needed`.
- Sets `RESUME_READY: yes` only if no blockers remain.

## Failure Conditions

- Writes application code during create mode.
- Omits dirty files.
- Uses vague standalone next steps such as "continue refactoring", "finish this", or "work on it".
- Prints loose, unversioned markers only.
- Omits the embedded `## Resume Prompt`.

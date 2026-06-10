# Context Packaging

Use this reference only when deciding what context belongs in a savepoint.

## Principle

A file `SAVEPOINT.md` is a recovery manifest. It is not:

- a chat transcript
- a full project memory
- a project-state database
- proof that code is correct
- a session-rotation controller

The goal is to give a fresh coding-agent session just enough checked context to continue safely.

## Context Budget

Prefer the smallest recoverable package:

1. Text savepoint: response text for explicit copy-paste/no-file transfer; no repo recovery guarantee.
2. File savepoint: one `.savepoint/SAVEPOINT.md` with disk/Git snapshot and validation state.
3. Detail spillover: focused `details/*.md` files only when file `SAVEPOINT.md` cannot stay both concise and recoverable.

For file `SAVEPOINT.md`, aim for about 120 lines or 5000 characters. For text savepoints, aim for about 20 lines or 1200 characters. Do not omit recovery-critical facts to fit the budget.

Never preserve raw chat transcripts, full diffs, long logs, shell history, or broad background unless the user explicitly asks and the content is essential and redacted.

## Durable State Files

Durable state files may include:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_STATE.md`
- `TASKS.md`
- `DECISIONS.md`
- `PLAN.md`
- `PLANS.md`
- issue/task files explicitly named by the user

When relevant, record path, why it matters, whether it was read, the section or anchor to read next, and any conflict with disk/Git state.

Do not copy whole state files into `SAVEPOINT.md`. Prefer path plus reason plus section.

## Detail Artifact Boundary

Durable state files are not detail artifacts.

`details/*.md` files are generated savepoint support artifacts used only for file detail spillover. They answer focused recovery questions that do not fit in `SAVEPOINT.md`.

Do not set `DETAILS_READY: yes` because durable state files exist. `DETAILS_READY` only describes generated `details/*.md` artifacts referenced by `SAVEPOINT.md`.

## Trust Order

On resume, trust sources in this order:

1. Current explicit user instruction in this session.
2. Current working tree and Git state.
3. Repository instructions and durable state files.
4. `SAVEPOINT.md`.
5. Focused detail artifacts referenced by `SAVEPOINT.md`.
6. Prior chat context only if explicitly provided by the user.

If a state file conflicts with disk state, disk state wins. Report the conflict before editing.

## Compression Rules

Keep only:

- current goal
- current state
- next action
- blocker
- changed, created, deleted, moved, and staged files
- loaded instructions and state files
- validation status
- risks and failed approaches
- observable done criteria
- next-session focus, if provided by the user
- suggested next-agent behavior, only when it changes how to resume

Cut:

- motivational text
- broad project background
- full conversation summaries
- repeated instructions already in `AGENTS.md` or `CLAUDE.md`
- speculative explanations
- generic coding best practices
- long lists of generic suggested skills
- skill recommendations that do not affect the next narrow action

## Safe Packaging Checklist

Set `RESUME_READY: yes` only when:

- `SAVEPOINT_MODE: file`
- disk/Git state was recorded
- changed files are listed
- relevant instruction/state files are listed, marked `none`, or marked `not-read` with a reason
- validation status is recorded
- secret redaction was checked
- next action is singular and executable
- no unresolved user question blocks continuation
- blockers are `none`

# Context Packaging

Use this reference only when deciding what context belongs in a handoff.

## Principle

`HANDOFF.md` is a verified recovery manifest. It is not:

- a chat transcript
- a full project memory
- a project-state database
- proof that code is correct
- a session-rotation controller

The goal is to give a fresh coding-agent session just enough verified context to continue safely.

## Context Budget

Prefer the smallest recoverable package:

1. `compact`: one `HANDOFF.md` can preserve the state.
2. `expanded`: `HANDOFF.md` links focused `details/*.md` files, each answering one recovery question.
3. `prompt-only`: no files are written; the response contains a continuation prompt.

For compact mode, aim for about 150 lines or 6000 characters. If that budget would hide recovery-critical facts, switch to expanded mode instead.

Never preserve raw chat history, full diffs, long logs, shell history, or broad background unless the user explicitly asks and the content is essential and redacted.

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

When relevant, record:

- path
- why it matters
- whether it was read
- the specific section or anchor to read next
- any conflict with disk/Git state

Do not copy whole state files into `HANDOFF.md`. Prefer path plus reason plus section.

## Detail Artifact Boundary

Durable state files are not detail artifacts.

`details/*.md` files are generated handoff support artifacts used only in expanded mode. They answer focused recovery questions that do not fit in compact `HANDOFF.md`.

Do not set `DETAIL_ARTIFACTS_READY: yes` because durable state files exist. `DETAIL_ARTIFACTS_READY` only describes generated `details/*.md` artifacts referenced by `HANDOFF.md`.

## Trust Order

On resume, trust sources in this order:

1. Current explicit user instruction in this session.
2. Current working tree and Git state.
3. Repository instructions and durable state files.
4. `HANDOFF.md`.
5. Focused detail artifacts referenced by `HANDOFF.md`.
6. Prior chat history only if explicitly provided by the user.

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
- broad project history
- full conversation summaries
- repeated instructions already in `AGENTS.md` or `CLAUDE.md`
- speculative explanations
- generic coding best practices
- long lists of generic suggested skills
- skill recommendations that do not affect the next narrow action

## Safe Packaging Checklist

Set `SAFE_FOR_NEW_SESSION: yes` only when:

- disk/Git state was recorded
- changed files are listed
- relevant instruction/state files are listed, marked `none`, or marked `not-read` with a reason
- validation status is recorded
- secret redaction was checked
- next action is singular and executable
- no unresolved user question blocks continuation
- blockers are `none`

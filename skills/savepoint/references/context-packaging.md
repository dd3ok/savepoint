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

Savepoints are current recovery artifacts, not history logs. Preserve older savepoints only when the user asks for history, audit, records, or preservation.

## Context Budget

Prefer the smallest recoverable package:

1. Text savepoint:
   - Response text for explicit text/copy-paste/no-file/no files/in-response/in the response transfer.
   - No repo recovery guarantee.
   - Use 300-600 tokens for simple copy-paste summaries.
   - Default to 800-1200 tokens for coding-agent transfers.
   - Allow up to 2000 tokens for complex cross-agent transfers.
   - If more is needed, create a file savepoint instead.
2. File savepoint:
   - One `.savepoint/SAVEPOINT.md` with disk/Git snapshot and validation state.
   - Aim for 1200-1800 tokens for clean-state, completed, or low-risk single-change recoverable transfers.
   - Default to 1500-2500 tokens when changes are multi-file, unresolved, risky, validation-heavy, or the working tree state is not straightforward.
   - Allow 2500-4000 tokens for complex ops, DB, PR, CI, or multi-agent work.
   - If top-level `SAVEPOINT.md` would exceed about 4000 tokens, move focused details to `details/*.md`.
3. Detail spillover:
   - Use focused `details/*.md` files only when `SAVEPOINT.md` cannot stay both concise and recoverable.
   - Top-level `SAVEPOINT.md` must say which detail file to read and why.

Budget guidance is advisory, not a validation rule. Path selection happens before budget: explicit text/copy-paste/no-file/no files/in-response/in the response requests remain text unless the user agrees to write a file.

These are budgets, not hard correctness limits. The top-level `SAVEPOINT.md` must still contain required markers, repo snapshot summary, validation status, changed-file summary, risks, and a singular next action. Do not omit recovery-critical facts solely to fit the budget; compress or spill over instead.

Never preserve raw chat transcripts, full diffs, long logs, shell history, or broad background unless the user explicitly asks and the content is essential and redacted.

Do not read `scripts/*.py` or `evals/*.json` during normal savepoint create/load. Run validators as commands; inspect validator/eval source only when debugging this skill.

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

Prefer:

- one-line values for required fields unless a concrete risk needs detail
- repo-relative paths for files under the recorded Git root
- absolute paths for `SAVEPOINT_PATH` and files outside the repo
- command summaries over passing logs
- recording each fact once; repeated next-step fields can point to the same narrow action

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

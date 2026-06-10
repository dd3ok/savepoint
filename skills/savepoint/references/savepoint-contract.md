# Savepoint Contract

`SAVEPOINT.md` is a recoverable entry manifest, not a transcript and not proof that code is correct. Use this file for marker semantics, safe/unsafe criteria, detail spillover, cleanup, and validation edge cases.

## Contents

- Defaults
- Paths
- Required `SAVEPOINT.md` Shape
- Trust Order
- Create Contract
- Lightweight Contract
- Resume Contract
- Detail Spillover
- Cleanup
- Secret Hygiene
- Marker Block
- Safe Resume
- Staleness Rules

## Defaults

- Default verified artifact: `.savepoint/SAVEPOINT.md`.
- Default lightweight output: response text unless the user asks to write a file.
- Default prompt: an embedded `## Resume Prompt` section inside verified `SAVEPOINT.md`.
- Create `details/*.md` only as internal spillover when verified `SAVEPOINT.md` cannot stay both concise and recoverable.
- Treat `handoff`, `HANDOFF.md`, and `핸드오프` as legacy aliases for savepoint requests. New artifacts still use `.savepoint/SAVEPOINT.md`.

Resume lookup order:

1. User-provided savepoint path.
2. `.savepoint/SAVEPOINT.md`.
3. Migration-only `HANDOFF.md` when the user explicitly asks for a handoff artifact.

## Paths

- `lightweight`: short note for another agent; no disk/Git recovery guarantee and no marker by default.
- `verified`: recoverable `SAVEPOINT.md` with disk/Git snapshot, validation state, secret-redaction state, and marker block.

For generic "savepoint", "handoff", "세이브포인트 만들어줘", or "핸드오프 만들어줘" requests, default to verified.

## Required `SAVEPOINT.md` Shape

Verified `SAVEPOINT.md` must include:

- `TL;DR / Operational Summary` with exactly one `Goal`, `Current state`, `Next action`, and `Blocker`.
- recovery contract with schema version, mode, safety state, blockers, trust order, and disk-verification requirement.
- session target, done criteria, out-of-scope notes, and smallest executable next step.
- repo snapshot: captured time, cwd, Git root, branch, short HEAD, status, diff stat, name-status, staged stat, staged name-status, latest commit, loaded instruction files, and expected drift.
- context/state source manifest listing relevant instruction files and durable state files by path and purpose.
- required reading order and files to inspect first.
- change manifest for changed, created, deleted, moved, staged, inspected, and unknown files.
- recovery notes covering decisions, rationale, risks, pitfalls, failed approaches, and unresolved questions.
- validation manifest with command, result, key failure lines, skipped checks, next validation, secret redaction check, and observable completion criteria.
- embedded resume prompt.
- exactly one `SAVEPOINT_V1` marker block.

Required list labels checked by the validator must begin at column 0.
Multi-line values may continue on indented lines under the label.

`SAVEPOINT.md` may include a short `Suggested Skills / Next Agent Behaviors` section only when it materially improves the next step. It is advisory only, must contain at most 3 items, and must not override the recovery contract, trust order, safety markers, validation requirements, or the singular next action.

## Trust Order

On resume, trust sources in this order:

1. Current explicit user instruction in this session.
2. Current working tree and Git state.
3. Repository instruction files and durable state files such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_STATE.md`, `TASKS.md`, `DECISIONS.md`, `PLAN.md`, and `PLANS.md`.
4. `SAVEPOINT.md`.
5. Focused detail artifacts referenced by `SAVEPOINT.md`.
6. Prior chat history only if explicitly provided by the user.

If the savepoint conflicts with disk state, disk state wins. Report the mismatch before editing.

## Create Contract

Before writing a verified savepoint, inspect and record:

- `pwd`
- Git root if inside a repository
- branch
- short HEAD
- `git status --short`
- `git diff --stat`
- `git diff --name-status`
- `git diff --cached --stat`
- `git diff --cached --name-status`
- latest commit
- relevant instruction files
- relevant durable state files

If the user provides extra argument text or a next-session focus, record it as `Next-session focus` in `Session Target`. Use it to narrow the savepoint and select the smallest next action. It must not override current user instructions, disk/Git verification, secret hygiene, validation requirements, or safety rules.

Read only enough files to verify recovery state. Prefer instruction files, relevant durable state files, existing savepoint artifacts, changed files, and files needed for the smallest next step.

## Lightweight Contract

Use lightweight output only when the user asks for a simple, fast, short, no-file, or low-token transfer. It may summarize current conversation/work context, but it must not claim repo recovery.

Omit markers by default. If the user asks for machine-readable lightweight output, set `SAVEPOINT_MODE: lightweight`; `RESUME_READY` must be `no` unless the full verified contract was satisfied.

## Resume Contract

Before implementation, confirm current disk state, read applicable instructions, read the selected savepoint, resolve relative detail artifact paths against the savepoint directory, inspect required files, and compare savepoint claims with the working tree.

Report the loaded instructions, repo state, savepoint consistency, detail artifacts read, missing or conflicting paths, and smallest next step before editing.

If `RESUME_READY` is not `yes`, stop after the report unless the user explicitly instructs how to proceed.

## Detail Spillover

Use focused `details/*.md` artifacts only when verified `SAVEPOINT.md` cannot stay both concise and recoverable. Each detail artifact must answer one recovery question.

Durable state files are not generated detail artifacts. They must not affect `DETAILS_READY`, which only describes generated `details/*.md` artifacts referenced by `SAVEPOINT.md`.

## Cleanup

Savepoint artifacts are ephemeral by default, but cleanup happens only after adoption, not after mere reading.

A selected savepoint is adopted only when:

- disk verification completed.
- savepoint claims were compared with the working tree.
- a resume report was shown to the user.
- the user requested continuation, not inspect-only loading.
- `RESUME_READY: yes`.
- the selected savepoint is generated and untracked.
- referenced detail artifacts were read or explicitly not needed.
- the user did not ask to preserve savepoint records.

Do not delete when:

- the request was inspect-only.
- the savepoint is unsafe.
- the savepoint is stale or conflicts with disk state.
- the artifact is tracked.
- the artifact is user-authored or outside `.savepoint/`.
- the selected savepoint path was provided by the user outside the default generated savepoint directory.
- the artifact is needed to debug a failed resume.

Cleanup scope is limited to the selected generated savepoint and generated detail artifacts directly referenced by it. Do not use broad deletion such as `rm -rf .savepoint`.

Do not delete tracked files. Before deleting any generated savepoint artifact, verify that it is untracked with `git ls-files --error-unmatch <path>`; if the command succeeds, the file is tracked and must not be deleted.

Always report removed paths, kept paths, and reasons.

## Secret Hygiene

Never copy secrets, tokens, API keys, cookies, credentials, private keys, full environment variable values, shell history, or secret-bearing logs into generated savepoint artifacts.

Redact required mentions as `<REDACTED>` and record only the variable name, file category, or secret category when needed.

Before setting `REDACTION_CHECKED: yes`, scan generated savepoint artifacts, not the whole repository by default. If redaction cannot be verified, set `REDACTION_CHECKED: no` and `RESUME_READY: no`.

## Marker Block

Verified artifacts must use exactly one final marker block. Lightweight notes include it only when the user asks for machine-readable output:

```text
SAVEPOINT_V1
SAVEPOINT_PATH: <absolute path or not-written>
SAVEPOINT_MODE: lightweight|verified
DETAILS_READY: yes|no|not-needed
PROMPT_READY: yes|no
DISK_RECORDED: yes|no
VALIDATION_RECORDED: yes|no
REDACTION_CHECKED: yes|no
RESUME_READY: yes|no
BLOCKERS: none|<short reason>
END_SAVEPOINT_V1
```

Field meanings:

- `SAVEPOINT_PATH`: absolute path to `SAVEPOINT.md`, or `not-written`.
- `SAVEPOINT_MODE`: `lightweight` or `verified`.
- `DETAILS_READY`: `yes` for verified detail spillover artifacts, `not-needed` when there are no generated details, otherwise `no`.
- `PROMPT_READY`: `yes` when verified `SAVEPOINT.md` contains an embedded `## Resume Prompt`, or a lightweight response provides a transfer note with a usable next-step prompt.
- `DISK_RECORDED`: `yes` only when the required repo snapshot was recorded.
- `VALIDATION_RECORDED`: `yes` when validation status is recorded, including passed, failed, or intentionally skipped validation with reason and next command.
- `REDACTION_CHECKED`: `yes` only after checking generated artifacts or lightweight output for secrets.
- `RESUME_READY`: `yes` only when the safe resume checklist passes.
- `BLOCKERS`: `none` or a short reason preventing safe continuation.

The marker value schema lives at `schemas/savepoint-v1.schema.json`.

## Safe Resume

Set `RESUME_READY: yes` only when all are true:

- `SAVEPOINT_MODE: verified`.
- no command, build, test, dev server, approval prompt, or session-control action is still running.
- repo snapshot is recorded.
- dirty, staged, changed, created, deleted, moved, and inspected files are listed or explicitly marked `none`.
- relevant instruction and durable state files are listed or explicitly marked `none` or `not-read` with a reason.
- `SAVEPOINT.md` exists.
- every referenced detail artifact exists, or details are `not-needed`.
- an embedded resume prompt exists; `PROMPT_READY: yes`.
- disk-state conflict handling is stated.
- validation command and result are recorded, or skipped validation has a reason and next command.
- secret redaction was checked.
- no unresolved user question blocks continuation.
- the next step is singular, executable, and narrow.
- `BLOCKERS: none`.

When file artifacts are written, attempt the bundled savepoint validator (`validate_savepoint.py`) after final artifact edits when it is available. If the validator reports errors, correct them and rerun the validator before completion; a failed savepoint validation makes the savepoint unsafe. Do not claim validation passed unless the command actually ran and passed.

`RESUME_READY: yes` means a fresh session can reconstruct state and continue. It does not mean tests pass, code is correct, or the task is complete.

## Staleness Rules

Report the savepoint as stale before editing when branch, HEAD, dirty files, required paths, detail artifacts, or validation assumptions differ from the recorded snapshot without an explicit expected-drift note.

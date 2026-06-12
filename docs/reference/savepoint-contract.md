# Savepoint Contract

`SAVEPOINT.md` is a recoverable entry manifest, not a transcript and not proof that code is correct. Use this file for marker semantics, safe/unsafe criteria, detail spillover, cleanup, and validation edge cases.

## Contents

- Defaults
- Paths
- Required `SAVEPOINT.md` Shape
- Trust Order
- Create Contract
- `/savepoint text` Contract
- Load / Resume Contract
- Detail Spillover
- Cleanup
- Secret Hygiene
- Marker Block
- Safe Resume
- Staleness Rules

## Defaults

- Default file artifact: `.savepoint/SAVEPOINT.md`.
- Default `/savepoint text` output: response text only.
- Default prompt: an embedded `## Resume Prompt` section inside file `SAVEPOINT.md`.
- Create `details/*.md` only as internal spillover when file `SAVEPOINT.md` cannot stay both concise and recoverable.

Resume lookup order:

1. User-provided savepoint path.
2. `.savepoint/SAVEPOINT.md`.

## Paths

- `text`: response-only note for another agent; no disk/Git recovery guarantee, no file, and no marker by default.
- `file`: Savepoint artifact with disk/Git snapshot, validation state, secret-redaction state, and marker block.

For generic "savepoint" or "세이브포인트 만들어줘" requests, default to file.

## Required `SAVEPOINT.md` Shape

File `SAVEPOINT.md` must include:

- `TL;DR / Operational Summary` with exactly one `Goal`, `Current state`, `Next action`, and `Blocker`.
- repo snapshot: captured time, cwd, Git root, branch, short HEAD, status, diff stat, name-status, staged stat, staged name-status, latest commit, loaded instruction files, and expected drift.
- context/state source manifest listing relevant instruction files and durable state files by path and purpose.
- required reading order and files to inspect first.
- change manifest for changed, created, deleted, moved, staged, inspected, and unknown files.
- recovery notes covering decisions, rationale, risks, pitfalls, and unresolved questions.
- validation manifest with command, result, key failure lines, skipped checks or none, next validation, secret redaction check, and observable completion criteria.
- embedded resume prompt.
- exactly one `SAVEPOINT_V1` marker block.

Required list labels checked by the validator must begin at column 0.
Multi-line values may continue on indented lines under the label.
The required shape describes recovery facts, not prose volume; routine savepoints should satisfy fields with terse values unless a concrete risk needs detail. Expanded template sections such as `Recovery Contract`, `Session Target`, and `Remaining Work` are allowed, but they are not required when the same safety facts are represented once elsewhere.

For token-efficient finalized artifacts, `scripts/render_savepoint.py` may render/finalize the Markdown from compact semantic JSON while preserving the v1 marker schema and safety checks. It should derive Git snapshot fields, marker values, redaction status, and savepoint-validation status instead of asking the agent to hand-write them.

After automatic context compaction, an intentional session reset, or an agent transfer, record recovery uncertainty in existing body fields such as `Expected drift`, `Unknown or unverified`, `Required Reading`, and `Recovery Notes`; do not add marker fields or new modes unless the marker schema is intentionally versioned.

`SAVEPOINT.md` may include a short `Suggested Skills / Next Agent Behaviors` section only when it materially improves the next step. It is advisory only, must contain at most 3 items, and must not override the recovery contract, trust order, safety markers, validation requirements, or the singular next action.

## Trust Order

On resume, trust sources in this order:

1. Current explicit user instruction in this session.
2. Current working tree and Git state.
3. Repository instruction files and durable state files such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_STATE.md`, `TASKS.md`, `DECISIONS.md`, `PLAN.md`, and `PLANS.md`.
4. `SAVEPOINT.md`.
5. Focused detail artifacts referenced by `SAVEPOINT.md`.
6. Prior chat context only if explicitly provided by the user.

If the savepoint conflicts with disk state, disk state wins. Report the mismatch before editing.

## Create Contract

Before writing a Savepoint, inspect and record:

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

When the next action touches files governed by nested or path-scoped instruction files, list those instruction files in Required Reading and record whether they were read or still need to be reloaded.

If the user provides extra argument text or a next-session focus, record it as `Next-session focus` in `Session Target`. Use it to narrow the savepoint and select the smallest next action. It must not override current user instructions, disk/Git verification, secret hygiene, validation requirements, or safety rules.

Read only enough files to verify recovery state. Prefer instruction files, relevant durable state files, existing savepoint artifacts, changed files, and files needed for the smallest next step.

## `/savepoint text` Contract

Use `/savepoint text` output only when the user explicitly asks for copy-paste, text, no-file/no files, in-response/in the response, or similar transfer. It may summarize current conversation/work context, but it must not claim repo recovery.

Omit markers by default. If the user asks for machine-readable text output, set `SAVEPOINT_MODE: text`, `SAVEPOINT_PATH: not-written`, and `RESUME_READY: no`.

## Load / Resume Contract

Before continuation or implementation, confirm current disk state, read applicable instructions, read the selected savepoint, resolve relative detail artifact paths against the savepoint directory, inspect required files, and compare savepoint claims with the working tree.

Report the loaded instructions, repo state, savepoint consistency, detail artifacts read, missing or conflicting paths, and smallest next step before editing.

Continue only when the user requested continuation and `RESUME_READY` is `yes`; inspect/load-only requests stop after the report.

## Detail Spillover

Use focused `details/*.md` artifacts only when file `SAVEPOINT.md` cannot stay both concise and recoverable. Each detail artifact must answer one recovery question.

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

## Adopted Overwrite

After an adopted generated default savepoint has been used for continuation, a later create/update request refreshes `.savepoint/SAVEPOINT.md` in place by default.

Default overwrite is allowed only when the existing artifact is the generated, untracked default `.savepoint/SAVEPOINT.md`, disk verification has just run, and the user did not ask to preserve history, audit records, or prior artifacts.

Treat a default savepoint as generated only when it is the default `.savepoint/SAVEPOINT.md`, untracked, contains exactly one valid final `SAVEPOINT_V1` marker block, passes savepoint validation, and was selected or adopted in the current workflow. Default path plus untracked status is not enough to prove generated authorship; if authorship is unclear, do not overwrite by default.

Never overwrite tracked, user-authored, external-path, inspect-only, stale, unsafe, conflicting, or debug-needed savepoints. Use renderer `--force` only after these adoption checks pass.

Preserve or rename old savepoints only when the user asks for history, audit, records, or preservation. Preserve directly referenced generated `details/*.md` artifacts together with the selected savepoint, and report old and new paths. When preserving a savepoint with generated details, keep the referenced detail files in the same relative layout or update the preserved savepoint references.

## Secret Hygiene

Never copy secrets, tokens, API keys, cookies, credentials, private keys, full environment variable values, shell history, or secret-bearing logs into generated savepoint artifacts.

Redact required mentions as `<REDACTED>` and record only the variable name, file category, or secret category when needed.

Before setting `REDACTION_CHECKED: yes`, scan generated savepoint artifacts, not the whole repository by default. If redaction cannot be verified, set `REDACTION_CHECKED: no` and `RESUME_READY: no`.

## Marker Block

File artifacts must use exactly one final marker block. Text notes include it only when the user asks for machine-readable output:

```text
SAVEPOINT_V1
SAVEPOINT_PATH: <absolute path or not-written>
SAVEPOINT_MODE: text|file
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
- `SAVEPOINT_MODE`: `text` or `file`.
- `DETAILS_READY`: `yes` for file detail spillover artifacts, `not-needed` when there are no generated details, otherwise `no`.
- `PROMPT_READY`: `yes` when file `SAVEPOINT.md` contains an embedded `## Resume Prompt`, or a text response provides a transfer note with a usable next-step prompt.
- `DISK_RECORDED`: `yes` only when the required repo snapshot was recorded.
- `VALIDATION_RECORDED`: `yes` when savepoint artifact validation and project validation posture are recorded, including passed, expected failed, or intentionally skipped project validation with reason and next command.
- `REDACTION_CHECKED`: `yes` only after checking generated artifacts or text output for secrets.
- `RESUME_READY`: `yes` only when the safe resume checklist passes.
- `BLOCKERS`: `none` or a short reason preventing safe continuation.

The marker value schema lives at `schemas/savepoint-v1.schema.json`.

## Safe Resume

Set `RESUME_READY: yes` only when all are true:

- `SAVEPOINT_MODE: file`.
- no command, build, test, dev server, approval prompt, or session-control action is still running.
- repo snapshot is recorded.
- dirty, staged, changed, created, deleted, moved, and inspected files are listed or explicitly marked `none`.
- relevant instruction and durable state files are listed or explicitly marked `none` or `not-read` with a reason.
- `SAVEPOINT.md` exists.
- every referenced detail artifact exists, or details are `not-needed`.
- an embedded resume prompt exists; `PROMPT_READY: yes`.
- disk-state conflict handling is stated.
- savepoint artifact validation ran and passed.
- project validation posture is recorded.
- secret redaction was checked.
- no unresolved user question blocks continuation.
- the next step is singular, executable, and narrow.
- `BLOCKERS: none`.

When file artifacts are written, attempt the bundled savepoint validator (`validate_savepoint.py`) after final artifact edits when it is available. If the validator reports errors, correct them and rerun the validator before completion; a failed savepoint validation makes the savepoint unsafe. Do not claim validation passed unless the command actually ran and passed.

`RESUME_READY: yes` means a fresh session can reconstruct state and continue. It does not mean tests pass, code is correct, or the task is complete.

Project validation posture uses these statuses:

- `passed`: project validation passed; `RESUME_READY: yes` is allowed.
- `failed-expected`: project validation failed in a known, documented way; `RESUME_READY: yes` is allowed only with reason and next validation command.
- `not-run-justified`: project validation was not run for a stated reason; `RESUME_READY: yes` is allowed only with reason and next validation command.
- `failed-blocking`: project validation failed in a blocking or unexplained way; `RESUME_READY: no`.
- `not-run-unknown`: project validation was not run without enough reason or next command; `RESUME_READY: no`.

## Staleness Rules

Report the savepoint as stale before editing when branch, HEAD, dirty files, required paths, detail artifacts, or validation assumptions differ from the recorded snapshot without an explicit expected-drift note.

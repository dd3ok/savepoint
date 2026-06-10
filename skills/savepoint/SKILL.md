---
name: savepoint
description: "Use when explicitly transferring coding-session state: create/update/load/inspect/resume .savepoint/SAVEPOINT.md by default, or create an explicit text/copy-paste savepoint. Not for SQL SAVEPOINT, ordinary summaries, docs, code changes, /new, /status, PTY, or session rotation. Triggers include 세이브포인트 만들어줘, 세이브포인트 읽고 이어서 해줘."
---

# Savepoint

Preserve coding-session state for continuation without prior chat context.

## Paths

- **Text savepoint**: response-only, copy-paste transfer for `복붙용`, `텍스트`, `파일 없이`, `붙여넣을`, `copy-paste`, `text`, `no-file`, `no files`, `in-response`, or `in the response` requests. Aim for about 1200 characters unless the user requests more. Do not claim repo recovery, disk/Git verification, `SAVEPOINT.md`, or `RESUME_READY: yes`. Omit markers by default; if markers are requested, use `SAVEPOINT_MODE: text`.
- **File savepoint**: default path for generic savepoint requests, `SAVEPOINT.md`, repo/Git state, validation, safe resume, or recovery by another coding agent. Write `.savepoint/SAVEPOINT.md`, include `## Resume Prompt`, and exactly one `SAVEPOINT_V1` block with `SAVEPOINT_MODE: file`.

## Rules

- Do not run `/new`, `/status`, control PTYs, rotate sessions, choose thresholds, or edit application code while creating.
- Use extra focus text only to narrow the next action.
- Redact secrets. Do not paste transcripts, full diffs, long logs, shell history, or duplicated PRDs/plans/ADRs/issues/commits.

## Create

1. For text savepoints, keep the response short and include only goal, state, next action, blockers/risks, and relevant paths or links.
2. For file savepoints, inspect and record cwd, Git root, branch, short HEAD, status, diff stat, name-status, staged stat, staged name-status, latest commit, relevant instruction files, and relevant durable state files.
3. Draft file artifacts with `references/savepoint-template.md`; use `details/*.md` only when `SAVEPOINT.md` cannot stay concise and recoverable.
4. Validate written artifacts with `skills/savepoint/scripts/validate_savepoint.py` or `scripts/validate_savepoint.py`; fix errors before setting `RESUME_READY: yes`.

## Load / Resume

1. Verify cwd, Git root, branch, short HEAD, status, and diff before trusting a savepoint.
2. Read applicable instructions and the selected savepoint: user path first, then `.savepoint/SAVEPOINT.md`.
3. Compare claims with the working tree; disk state wins, and drift must be reported before edits.
4. Continue only when the user requested continuation and `RESUME_READY` is `yes`; otherwise stop after the report.
5. Cleanup only adopted, generated, untracked artifacts. For inspect-only requests, do not clean up by default.

For text savepoints, do not read references unless asked. For file create, start with `references/savepoint-template.md`. For file create/load/inspect/resume, read `references/savepoint-contract.md` only for unclear marker, `RESUME_READY`, cleanup, staleness, or detail-spillover rules. Read `references/context-packaging.md` only for state-file/context-budget questions.

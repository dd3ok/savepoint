---
name: savepoint
description: "Use when explicitly transferring coding-session state: create/update/inspect/resume .savepoint/SAVEPOINT.md or a lightweight note. Not for SQL SAVEPOINT, ordinary summaries, docs, code changes, /new, /status, PTY, or session rotation. Triggers include 세이브포인트 만들어줘, 세이브포인트 읽고 이어서 해줘."
---

# Savepoint

Preserve coding-session state for continuation without prior chat context.

## Paths

- **Lightweight note**: response-only transfer for `간단`, `빠른`, `요약`, `3000자`, `파일 없이`, or low-token requests. Aim for about 1200 characters unless the user requests more. Do not claim repo recovery, disk/Git verification, `SAVEPOINT.md`, or `RESUME_READY: yes`. Omit markers by default.
- **Verified savepoint**: `.savepoint/SAVEPOINT.md` for generic savepoint requests, `SAVEPOINT.md`, repo/Git state, validation, safe resume, or recovery by another coding agent. Include `## Resume Prompt` and exactly one `SAVEPOINT_V1` block.

## Rules

- Do not run `/new`, `/status`, control PTYs, rotate sessions, choose thresholds, or edit application code while creating.
- Use extra focus text only to narrow the next action.
- Redact secrets. Do not paste transcripts, full diffs, long logs, shell history, or duplicated PRDs/plans/ADRs/issues/commits.

## Create

1. For lightweight, keep the response short and include only goal, state, next action, blockers/risks, and relevant paths or links.
2. For verified, inspect and record cwd, Git root, branch, short HEAD, status, diff stat, name-status, staged stat, staged name-status, latest commit, relevant instruction files, and relevant durable state files.
3. Draft verified artifacts with `references/savepoint-template.md`; use `details/*.md` only when `SAVEPOINT.md` cannot stay concise and recoverable.
4. Validate written artifacts with `skills/savepoint/scripts/validate_savepoint.py` or `scripts/validate_savepoint.py`; fix errors before setting `RESUME_READY: yes`.

## Resume

1. Verify cwd, Git root, branch, short HEAD, status, and diff before trusting a savepoint.
2. Read applicable instructions and the selected savepoint: user path first, then `.savepoint/SAVEPOINT.md`.
3. Compare claims with the working tree; disk state wins, and drift must be reported before edits.
4. If `RESUME_READY` is not `yes`, stop after the report unless the user explicitly instructs how to proceed.
5. Cleanup only adopted, generated, untracked artifacts. For inspect-only requests, do not clean up by default.

For lightweight notes, do not read references unless asked. For verified create, start with `references/savepoint-template.md`; read `references/savepoint-contract.md` only for unclear marker, `RESUME_READY`, cleanup, staleness, or detail-spillover rules. Read `references/context-packaging.md` only for state-file/context-budget questions.

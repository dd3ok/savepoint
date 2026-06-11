---
name: savepoint
description: "Use when explicitly creating/updating/loading/inspecting/resuming coding-session savepoints: .savepoint/SAVEPOINT.md or text/copy-paste. Not for SQL SAVEPOINT, ordinary summaries, docs, code changes, /new, /status, PTY, or session rotation. Triggers: 세이브포인트 만들어줘; 세이브포인트 로드해줘; 세이브포인트 읽어줘; 세이브포인트 이어서 해줘."
---

# Savepoint

Preserve coding-session state for continuation without prior chat context.

## Choose

- **Quick Save**: response-only text for explicit `복붙용`, `텍스트`, `파일 없이`, `붙여넣을`, `copy-paste`, `text`, `no-file`, `no files`, `in-response`, or `in the response` requests. Do not claim recovery, disk/Git verification, `SAVEPOINT.md`, or `RESUME_READY: yes`. Omit markers unless requested; then use `SAVEPOINT_MODE: text`.
- **Savepoint**: default recoverable file checkpoint for generic requests, `SAVEPOINT.md`, repo/Git state, validation, safe resume, or recovery by another coding agent. Generate `.savepoint/SAVEPOINT.md` with `scripts/render_savepoint.py`, include `## Resume Prompt`, and exactly one `SAVEPOINT_V1` block with `SAVEPOINT_MODE: file`.

## Rules

- Normal use: do not read references, `scripts/*.py`, or `evals/*.json`; run the renderer and validator as commands and inspect their outputs.
- Stay in artifact scope: do not run `/new`, `/status`, control PTYs, rotate sessions, choose thresholds, or edit application code while creating.
- Use extra focus text only to narrow the next action. Redact secrets. Do not paste transcripts, full diffs, long logs, shell history, or duplicated PRDs/plans/ADRs/issues/commits.

## Create

1. For Quick Saves, include only goal, state, next action, blockers/risks, and relevant paths or links.
2. For Savepoints, inspect and record cwd, Git root, branch, short HEAD, status, diff stat, name-status, staged stat, staged name-status, latest commit, relevant instruction files, and relevant durable state files.
3. Run `python3 scripts/render_savepoint.py --input <input.json> --assert-no-active-commands --scan-redaction --run-savepoint-validation` from compact semantic JSON, then inspect only the generated `.savepoint/SAVEPOINT.md`.
4. Renderer input minimum fields: `goal`, `current_state`, `next_action`; for ready Savepoints, also record passing `project_validation`. Do not read renderer source to discover input shape.
5. Renderer exit code `2` can still mean a not-ready `SAVEPOINT.md` was written. Inspect the file, report blockers, and do not continue unless `RESUME_READY: yes`.
6. For adopted generated default savepoints, later create/update requests refresh `.savepoint/SAVEPOINT.md` in place unless the user asks to preserve history.
7. Validate written artifacts with `skills/savepoint/scripts/validate_savepoint.py` or `scripts/validate_savepoint.py`; fix errors before setting `RESUME_READY: yes`.

## Load / Resume

1. Verify cwd, Git root, branch, short HEAD, status, and diff before trusting a savepoint.
2. Read applicable instructions and the selected savepoint: user path first, then `.savepoint/SAVEPOINT.md`.
3. Compare claims with the working tree; disk state wins, and drift must be reported before edits.
4. Continue only when the user requested continuation and `RESUME_READY` is `yes`; otherwise stop after the report.
5. Cleanup only adopted, generated, untracked artifacts. For inspect-only requests, do not clean up by default.

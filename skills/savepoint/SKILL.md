---
name: savepoint
description: "Create or load a recoverable coding-session checkpoint at .savepoint/SAVEPOINT.md so a fresh agent can resume from current repo/Git state. Use for context reset, session transfer, 세이브포인트 만들어줘, 세이브포인트 로드해줘, 세이브포인트 읽어줘, 세이브포인트 이어서 해줘. Not for SQL SAVEPOINT, ordinary summaries, direct code/docs edits without checkpoint intent, /status, /new, PTY/session control, session rotation, or app features named savepoint."
argument-hint: "[save|load|text] [next-session focus]"
---

# Savepoint

Create/load a recoverable repo/Git checkpoint without prior chat context.

Modes:
- default or `save`: create or refresh `.savepoint/SAVEPOINT.md`
- `load`: verify an existing savepoint and report whether continuation is safe
- `text`: response-only copy-paste handoff; no file recovery guarantee

If slash prompts are unavailable, treat natural-language `$savepoint` requests the same way.

## Rules

- During save/load verification, stay in savepoint scope; do not edit application code.
- Resolve `<savepoint-skill-dir>` before running commands; Claude Code: `${CLAUDE_SKILL_DIR}`.
- Do not run `/new`, `/status`, PTY/session rotation, threshold policy, or background process control.
- Run the bundled CLI; do not inspect implementation source during normal use.
- Prefer current disk/Git/durable state over chat memory.
- Do not paste transcripts, diffs, logs, shell history, PRDs, ADRs, issues, or commits; cite paths, URLs, branches, or commits.
- Redact API keys, tokens, cookies, credentials, private keys, passwords, `.env` values, and PII as `<redacted>`; never put raw secrets in input.
- File savepoints must end with exactly one `SAVEPOINT_V1` marker block.
- Keep top-level `SAVEPOINT.md` compact; use generated `details/*.md` only when needed.

## Create / Save

1. Treat any focus text only as next-session focus.
2. Capture repo/Git state in compact input JSON with `goal`, `current_state`, `next_action`, `files_to_inspect_first`, and `unresolved_blockers`; if blank, start with `python3 <savepoint-skill-dir>/scripts/savepoint.py init-input --output .savepoint/input.json`.
3. Set `validation.project.status` to `passed`, `failed-expected`, `failed-blocking`, `not-run-justified`, or `not-run-unknown`. `failed-expected` needs failed command/result/summary evidence, reason, and next validation command. `not-run-justified` needs reason and next validation command.
4. Run `python3 <savepoint-skill-dir>/scripts/savepoint.py save --input .savepoint/input.json --output .savepoint/SAVEPOINT.md --assert-no-active-commands --scan-redaction --validate`; in this repo, `python3 scripts/savepoint.py save ...` also works.
5. Inspect only the generated `.savepoint/SAVEPOINT.md`.
6. Report exact path, `RESUME_READY`, blockers if any, and the first next action.

Exit code `2` may still write a not-ready `SAVEPOINT.md`; inspect it, report blockers, and do not continue unless `RESUME_READY: yes`.

## Load / Resume

1. Select the user path first, otherwise `.savepoint/SAVEPOINT.md`; run `python3 <savepoint-skill-dir>/scripts/savepoint.py inspect <path> --json`.
2. Verify cwd, Git root, branch, short HEAD, status, and diff against disk state.
3. Disk state wins over savepoint text. Report drift before edits.
4. Continue only when the user requested continuation and `RESUME_READY` is `yes`, with no blocking drift or missing required file.
5. For inspect-only requests, do not clean up by default.

## Text Mode

Use text mode only when the user explicitly asks for copy-paste, text-only, `no-file`, `no files`, `in-response`, or `in the response`.

Prepare `.savepoint/input.json` as in Save, then run `python3 <savepoint-skill-dir>/scripts/savepoint.py text --input .savepoint/input.json`.

Text mode must not claim `.savepoint/SAVEPOINT.md` was written, recovery is guaranteed, or `RESUME_READY: yes`.

## Advanced Cases

Read references only when normal CLI use is insufficient: `references/contract.md` for marker/safe-resume/cleanup/staleness/detail/overwrite edge cases, `references/safety.md` for secret-like paths, and `references/template.md` when the renderer is unavailable.

For refresh, append `--force` only when the existing file is the generated, untracked, valid default artifact `.savepoint/SAVEPOINT.md` and the user did not ask to preserve history; otherwise preserve or ask.

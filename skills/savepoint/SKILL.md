---
name: savepoint
description: "Create or load a recoverable coding-session checkpoint at .savepoint/SAVEPOINT.md so a fresh agent can resume from current repo/Git state. Use for context reset, session transfer, 세이브포인트 만들어줘, 세이브포인트 로드해줘, 세이브포인트 읽어줘, 세이브포인트 이어서 해줘. Not for SQL SAVEPOINT, ordinary summaries, direct code/docs edits without checkpoint intent, /status, /new, or app features named savepoint."
argument-hint: "[save|load|text] [next-session focus]"
---

# Savepoint

Use this skill to preserve or load coding-session state without relying on prior chat context.

Default behavior:

```text
/savepoint        -> create or refresh `.savepoint/SAVEPOINT.md`
/savepoint save   -> same as default
/savepoint load   -> verify an existing savepoint and report whether continuation is safe
/savepoint text   -> response-only copy-paste handoff; no file recovery guarantee
```

Native slash-command support depends on the client. If slash prompts are not passed through, use `$savepoint` natural language requests.

## Rules

- Stay in savepoint scope. Do not edit application code.
- Do not run `/new`, `/status`, PTY/session rotation, threshold policy, or background process control.
- Do not read references, `scripts/*.py`, or `evals/*.json` during normal use.
- Prefer current files, Git state, and durable state files over chat memory.
- Do not paste transcripts, full diffs, long logs, shell history, PRDs, ADRs, issues, or commits.
- Reference existing artifacts by path, URL, branch, or commit.
- Redact API keys, tokens, cookies, credentials, private keys, passwords, `.env` values, and PII as `<redacted>`.
- File savepoints must end with exactly one `SAVEPOINT_V1` marker block.
- Keep top-level `SAVEPOINT.md` compact. Use generated `details/*.md` only when needed for recovery.

## Create / Save

1. Use the provided focus text, if any, only to narrow the next action.
2. Capture repo state: cwd, Git root, branch, short HEAD, `git status --short`, diff stat, name-status, staged stat, staged name-status, latest commit, instruction files, and durable state files.
3. Write compact input JSON with at least `goal`, `current_state`, `next_action`, `files_to_inspect_first`, `unresolved_blockers`, and `validation.project.status`. If starting from blank, use `python3 <savepoint-skill-dir>/scripts/savepoint.py init-input --output .savepoint/input.json`; its default project validation status is `not-run-unknown`.
4. Use project validation status exactly as one of `passed`, `failed-expected`, `failed-blocking`, `not-run-justified`, or `not-run-unknown`. For `failed-expected` or `not-run-justified`, include a reason and next validation command.
5. Run:

```bash
python3 <savepoint-skill-dir>/scripts/savepoint.py save --input .savepoint/input.json --output .savepoint/SAVEPOINT.md --assert-no-active-commands --scan-redaction --validate
```

Inside this repository, `python3 scripts/savepoint.py save ...` also works.

6. For refresh, append `--force` only when the existing file is the generated, untracked, valid default artifact `.savepoint/SAVEPOINT.md` and the user did not ask to preserve history; otherwise preserve or ask.
7. Inspect only the generated `.savepoint/SAVEPOINT.md`.
8. Report exact path, `RESUME_READY`, blockers if any, and the first next action.

Renderer exit code `2` can still mean a not-ready `SAVEPOINT.md` was written. Inspect the file, report blockers, and do not continue unless `RESUME_READY: yes`.

## Load / Resume

1. Read the selected savepoint: user path first, then `.savepoint/SAVEPOINT.md`.
2. Verify cwd, Git root, branch, short HEAD, status, and diff against current disk state.
3. Disk state wins over savepoint text. Report drift before edits.
4. Continue only when the user requested continuation and `RESUME_READY` is `yes`, with no blocking drift or missing required file.
5. For inspect-only requests, do not clean up by default.

## Text Mode

Use text mode only when the user explicitly asks for copy-paste, text-only, `no-file`, `no files`, `in-response`, or `in the response`.

Run:

```bash
python3 <savepoint-skill-dir>/scripts/savepoint.py text --input .savepoint/input.json
```

Text mode must not claim `.savepoint/SAVEPOINT.md` was written, repo recovery is guaranteed, or `RESUME_READY: yes`.

## Advanced Cases

Read `references/contract.md` only when marker semantics, cleanup, stale savepoints, detail spillover, overwrite adoption, or safe-resume edge cases are unclear.

Read `references/safety.md` only when secret redaction or secret-like paths are involved.

Read `references/template.md` only when the renderer is unavailable and a manual artifact is unavoidable.

---
name: new-session-handoff
description: "Use only when the user explicitly asks to create or resume HANDOFF.md artifacts for coding-agent session transfer, asks for a new-session continuation prompt, or says 핸드오프 만들어줘 / 핸드오프 읽고 이어서 해줘. Does not run /new, control PTYs, or modify application code while creating a handoff."
---

# New Session Handoff

Prepare a fresh coding-agent session to continue work without prior chat history.

This is an artifact-only skill. Do not run `/new`, `/status`, control PTYs, rotate sessions, choose context thresholds, or claim that a reset happened. External orchestrators own those actions.

## Default Output

Create one lightweight file unless the user asks otherwise:

```text
.new-session-handoff/HANDOFF.md
```

Do not create `NEW_SESSION_PROMPT.txt` by default. Embed the resume prompt inside `HANDOFF.md`.

Create `details/*.md` only when expanded mode is needed because `HANDOFF.md` cannot stay both compact and recoverable.

## Create Handoff

Use when the user asks to create a handoff, preserve context for a fresh session, prepare a new-session prompt, or says `핸드오프 만들어줘`.

1. Inspect disk state before summarizing: `pwd`, Git root if any, branch, short HEAD, `git status --short`, `git diff --stat`, `git diff --name-status`, staged diff state, latest commit, and relevant instruction files.
2. Read only what is needed to recover: instruction files, existing handoff artifacts, changed files, and files needed for the smallest next step.
3. Write verified facts only. Mark unknowns as `Unknown` or `확인 필요`.
4. Keep the handoff short: no raw transcript, full diff, long logs, shell history, or speculative background.
5. Include one narrow next action and an embedded `## Resume Prompt`.
6. Include exactly one final `HANDOFF_AUTOMATION_V1` marker block.
7. Check generated artifacts for secrets before marking them safe.

Read `references/handoff-template.md` when drafting `HANDOFF.md`. Read `references/handoff-contract.md` only when marker semantics, safe/unsafe criteria, cleanup, or validation rules are ambiguous.

## Resume From Handoff

Use when the user asks to read a handoff, continue from a handoff, or says `핸드오프 읽고 이어서 작업` or `핸드오프 읽고 이어서 해줘`.

1. Confirm current cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
2. Read applicable instruction files.
3. If the user provided a handoff path, read that path as the selected handoff. Otherwise, look for `.new-session-handoff/HANDOFF.md`, then legacy `HANDOFF.md`, and use the first existing handoff.
4. Compare handoff claims with the working tree. If they conflict, trust disk state and report the mismatch.
5. Report loaded instructions, repo state, handoff consistency, missing or conflicting paths, and the first implementation step.
6. If `SAFE_FOR_NEW_SESSION` is not `yes`, stop after the report unless the user explicitly instructs how to proceed.
7. After reporting a verified safe resume, delete only untracked generated handoff artifacts unless the user asked to keep them.

If the user asked only to inspect or resume context, stop after the report and any eligible cleanup. Do not implement. If they explicitly asked to continue implementation and the handoff is safe, proceed with only the smallest remaining task under the repository instructions.

## Safety Rules

Never copy secrets, tokens, API keys, cookies, credentials, private keys, full environment values, shell history, or secret-bearing logs into handoff artifacts. Redact required mentions as `<REDACTED>`.

Do not delete tracked files. Before deleting a handoff artifact, check that it is generated and untracked.

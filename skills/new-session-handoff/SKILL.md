---
name: new-session-handoff
description: "Use only when the user explicitly asks to create, update, inspect, or resume HANDOFF.md artifacts for coding-agent session transfer, asks for a new-session continuation prompt, or says 핸드오프 만들어줘 / 핸드오프 읽고 이어서 해줘. Do not use for ordinary summaries, README/docs writing, AGENTS.md authoring alone, application-code changes, /new, /status, PTY control, or session-rotation policy."
---

# New Session Handoff

Prepare a fresh coding-agent session to continue work without prior chat history.

This is an artifact-only skill. Do not run `/new`, `/status`, control PTYs, rotate sessions, choose context thresholds, or claim that a reset happened. External orchestrators own those actions.

## Default Output

Create one lightweight file unless the user asks otherwise:

```text
.new-session-handoff/HANDOFF.md
```

Embed the resume prompt inside `HANDOFF.md`.

Create `details/*.md` only when expanded mode is needed because `HANDOFF.md` cannot stay both compact and recoverable.

## When Not To Use

Do not use this skill for ordinary conversation summaries, README generation, AGENTS.md/CLAUDE.md authoring alone, code implementation, slash-command execution, PTY/session orchestration, or context-window threshold policy.

## Context Packaging

A handoff is a verified recovery manifest, not memory, not a transcript, and not proof that code is correct. Include only context required for the next session to reconstruct state: goal, current disk/Git snapshot, loaded instructions/state files, changed files, validation state, risks, and one narrow next action.

If project state files such as `AGENTS.md`, `CLAUDE.md`, `PROJECT_STATE.md`, `TASKS.md`, `DECISIONS.md`, `PLAN.md`, or `PLANS.md` are relevant, list their paths and the specific reason to read them. Do not paste whole state files into `HANDOFF.md`.

Durable state files are not generated detail artifacts and must not affect `DETAIL_ARTIFACTS_READY`.

Read `references/context-packaging.md` when deciding whether to use compact, expanded, or prompt-only mode, or when project state files conflict with disk state.

## Create Handoff

Use when the user asks to create a handoff, preserve context for a fresh session, prepare a new-session prompt, or says `핸드오프 만들어줘`.

1. Inspect disk state before summarizing: `pwd`, Git root if any, branch, short HEAD, `git status --short`, `git diff --stat`, `git diff --name-status`, staged diff state, latest commit, relevant instruction files, and relevant durable state files.
2. Read only what is needed to recover: instruction files, relevant durable state files, existing handoff artifacts, changed files, and files needed for the smallest next step.
3. Write verified facts only. Mark unknowns as `Unknown` or `확인 필요`.
4. Keep the handoff short: no raw transcript, full diff, long logs, shell history, or speculative background.
5. Include one narrow next action and an embedded `## Resume Prompt`.
6. Include exactly one final `HANDOFF_AUTOMATION_V1` marker block.
7. Check generated artifacts for secrets before marking them safe.

Read `references/handoff-template.md` when drafting `HANDOFF.md`. Read `references/handoff-contract.md` only when marker semantics, safe/unsafe criteria, cleanup, or validation rules are ambiguous. Read `references/context-packaging.md` for state-file and mode-selection boundaries.

## Resume From Handoff

Use when the user asks to read a handoff, continue from a handoff, or says `핸드오프 읽고 이어서 작업` or `핸드오프 읽고 이어서 해줘`.

1. Confirm current cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
2. Read applicable instruction files.
3. If the user provided a handoff path, read that path as the selected handoff. Otherwise, look for `.new-session-handoff/HANDOFF.md`, then legacy `HANDOFF.md`, and use the first existing handoff.
4. Compare handoff claims with the working tree. If they conflict, trust disk state and report the mismatch.
5. Report loaded instructions, repo state, handoff consistency, missing or conflicting paths, and the first implementation step.
6. If `SAFE_FOR_NEW_SESSION` is not `yes`, stop after the report unless the user explicitly instructs how to proceed.
7. After reporting a verified safe resume, delete only untracked generated handoff artifacts that were adopted for this resume unless the user asked to keep them.

A handoff is adopted only after it was selected, read, compared against current disk state, reported to the user, found `SAFE_FOR_NEW_SESSION: yes`, and used for a resume/continue request rather than inspect-only context loading.

For inspect-only requests, do not clean up by default. Stop after the report. If the user asked to resume/continue and the handoff is safe, perform any eligible adopted-artifact cleanup, then proceed only with the smallest remaining task when implementation was explicitly requested.

## Safety Rules

Never copy secrets, tokens, API keys, cookies, credentials, private keys, full environment values, shell history, or secret-bearing logs into handoff artifacts. Redact required mentions as `<REDACTED>`.

Do not delete tracked files. Before deleting a handoff artifact, check that it is adopted, generated, and untracked. Never delete unsafe handoffs, stale or conflicting handoffs, external handoff paths, user-authored files, or artifacts needed to debug a failed resume.

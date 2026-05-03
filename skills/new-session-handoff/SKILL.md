---
name: new-session-handoff
description: Create or resume a verified HANDOFF.md for coding-agent session transfer when context is full, after compaction/session rotation, or when switching agents. Captures repo state, changed files, decisions, validation, pitfalls, risks, and the next safe step. Triggers: 핸드오프 만들어줘, 핸드오프 읽고 이어서.
---

# New Session Handoff

## Purpose

Prepare or resume a fresh coding-agent session without relying on prior chat history, hidden reasoning, tool output, or compacted context.

This skill must not run interactive session commands such as Codex `/new`, control an agent CLI, or rotate sessions. In create mode, it writes handoff artifacts only and must not modify application code.

Create mode is read-mostly. It may write `HANDOFF.md`, `NEW_SESSION_PROMPT`, or focused handoff detail artifacts only. It must not edit application code, run broad refactors, install dependencies, or start long-running commands.

This is an artifact-only skill. `/status`, `/new`, PTY control, context-threshold policy, and session rotation belong to external orchestrators, not this skill.

## Core Policy

Recoverability first. Compactness second.

`HANDOFF.md` is always the recoverable entry manifest. For small or medium tasks, it may contain all details. For large tasks, it must remain the landing page and required reading order for focused detail artifacts.

For large tasks, use `HANDOFF.md` as an entry manifest plus focused detail artifacts, for example `handoffs/architecture.md`, `handoffs/changed-files.md`, `handoffs/validation.md`, `handoffs/pitfalls.md`, or another user-requested path.

Default size policy:

- Small or medium tasks: keep `HANDOFF.md` compact and scannable, roughly under 100-150 lines when that does not lose recovery information.
- Large architecture or multi-file tasks: do not force all context into a fixed line budget. Keep `HANDOFF.md` compact and move detailed rationale, validation logs, change ledgers, and pitfalls into focused artifacts.
- A fresh session reads `HANDOFF.md` first, then only the detail artifacts needed for the smallest next step.

Never compress away:

- verified decisions and rationale
- changed, created, deleted, or inspected files
- validation commands and results
- known risks, pitfalls, and failed approaches
- unresolved questions
- the smallest executable next step

A short handoff that loses critical recovery information is worse than a longer handoff with clear structure.

## Secret Hygiene

Never copy secrets, tokens, API keys, cookies, private credentials, private keys, full environment variable values, shell history, or unredacted secret-bearing logs into `HANDOFF.md`, `NEW_SESSION_PROMPT`, or detail artifacts.

Redact values as `<REDACTED>` and record only the variable name, file category, or secret category when needed. If secret redaction cannot be verified, set `SECRET_REDACTION_CHECKED: no` and `SAFE_FOR_NEW_SESSION: no`.

## Create Handoff

Use this mode when the user asks to make a handoff, says `핸드오프 만들어줘` or `핸드오프 문서 만들어줘`, save `HANDOFF.md`, prepare a new-session prompt, or preserve context before a new session.

1. Inspect current state before summarizing:
   - `pwd`
   - `git rev-parse --show-toplevel` if inside a Git repository
   - `git branch --show-current`
   - `git rev-parse --short HEAD`
   - `git status --short`
   - `git diff --stat`
   - `git diff --name-status`
   - `git diff --cached --stat`
   - `git log -1 --oneline`
   - relevant instruction files: `AGENTS.md`, `AGENTS.override.md`, `PLANS.md`, `PLAN.md`, `HANDOFF.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/**`, `.claude/**`

2. Read enough files to verify recovery state.
   - Prefer instruction files, current handoff artifacts, changed files, and files needed for the next step.
   - Do not expand into implementation investigation beyond what is needed to create a recoverable handoff.

3. Summarize only verified facts.
   - Do not invent file paths, commands, test results, branch names, or decisions.
   - Mark unknowns as `확인 필요` or `Unknown`.
   - Prefer exact paths and exact commands.
   - Keep log snippets short and include only lines needed to identify the result or failure.

4. Choose the size strategy:
   - Small or medium task: write one compact manifest `HANDOFF.md`.
   - Large task: write `HANDOFF.md` as the entry manifest and create focused detail artifacts. Each artifact must answer one recovery question, such as what architecture changed, what files changed, what validation ran, what failed, or what remains.
   - Do not create raw transcript dumps, long logs, or full diffs unless the user explicitly asks and they are essential for recovery.

5. Produce the requested artifact(s):
   - `NEW_SESSION_PROMPT`: a copy-paste prompt for a fresh agent session.
   - `HANDOFF.md`: a self-contained entry manifest.
   - Optional focused detail artifacts for large tasks.

6. Write only what the user requested:
   - If asked to create a handoff, write or update `HANDOFF.md` by default unless another path was requested.
   - If asked only for a prompt, do not write files; embed a self-contained Markdown handoff draft in the prompt instead of pointing to `HANDOFF.md`.

7. Make the handoff recoverable.
   - The next session must be able to continue from the repository state and the handoff artifacts alone.
   - If the handoff conflicts with the actual working tree, instruct the next session to trust the working tree.
   - Include the smallest safe first step, not only a broad to-do list.
   - If detail artifacts are used, include a required reading order in `HANDOFF.md`.

8. End with markers for automation:

   ```text
   HANDOFF_AUTOMATION_V1
   HANDOFF_READY: <absolute path or not-written>
   HANDOFF_SCHEMA_VERSION: 1
   HANDOFF_MODE: compact|expanded|prompt-only
   DETAIL_ARTIFACTS_READY: yes|no|not-needed
   NEW_SESSION_PROMPT_READY: yes|no
   DISK_STATE_RECORDED: yes|no
   VALIDATION_RECORDED: yes|no
   SECRET_REDACTION_CHECKED: yes|no
   SAFE_FOR_NEW_SESSION: yes|no
   BLOCKERS: none|<short reason>
   END_HANDOFF_AUTOMATION_V1
   ```

   Use `SAFE_FOR_NEW_SESSION: yes` only when all are true:
   - No command, build, test, dev server, or approval prompt is still running.
   - Current repo state was recorded: cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
   - Changed, created, deleted, moved, staged, or inspected files are listed or explicitly marked `none`.
   - Every referenced detail artifact exists, or expanded artifacts are explicitly `not-needed`.
   - Validation command and result are recorded, or skipped validation has an explicit low-risk reason and a next validation command.
   - Secret redaction was checked.
   - No unresolved user question blocks the next session.
   - The next step is singular and executable.

## Resume From Handoff

Use this mode when the user asks to continue from a handoff, read `HANDOFF.md`, or says `핸드오프 읽고 작업해줘`, `핸드오프 문서 읽고 작업해줘`, or `핸드오프 보고 이어서 작업`.

1. Establish context before implementing:
   - Confirm `pwd`, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
   - Read applicable instruction files and `HANDOFF.md`.
   - If `HANDOFF.md` contains a required reading order, read only the focused detail artifacts needed for the smallest next step.
   - Inspect files listed under `Files to inspect first`, `Required Reading`, and `Change Manifest`.
   - Verify that referenced paths exist or report missing paths before editing.

2. Compare `HANDOFF.md` with the actual working tree.
   - If they conflict, trust the working tree and report the mismatch.
   - Mark missing or uncertain handoff details as `확인 필요` or `Unknown`.

3. Report before editing:
   - Loaded instructions
   - Repo state
   - Handoff consistency
   - Detail artifacts read, if any
   - Missing or conflicting paths, if any
   - Smallest next step

4. If `SAFE_FOR_NEW_SESSION` is not `yes`, stop after the report unless the user explicitly instructs you how to proceed.

5. If the user asked only to inspect or resume context, stop after the report. If the user explicitly asked to continue implementation and verification is safe, proceed with only the smallest remaining task, following repository instructions and running the narrowest relevant validation after changes.

## Templates

Read the matching one-level reference before drafting each artifact:

- Read `references/handoff-template.md` when producing or updating `HANDOFF.md`.
- Read `references/new-session-prompt-template.txt` when producing `NEW_SESSION_PROMPT`.
- Read `references/expanded-artifacts.md` before creating focused detail artifacts.
- Read `references/quality-checklist.md` before setting `SAFE_FOR_NEW_SESSION: yes`.
- Read `references/marker-semantics.md` before printing automation markers.

## Automation Boundary

External agents such as Hermes or OpenClaw may use the final markers to decide when to send a session-reset command to an agent CLI PTY. This skill itself must not claim to execute `/new` or any other interactive reset command; it only prepares safe continuation artifacts.

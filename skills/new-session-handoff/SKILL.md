---
name: new-session-handoff
description: Creates or resumes a compact HANDOFF.md for coding-agent session handoff. Use when context is nearly full, after compaction/session rotation, or when the user asks for handoff, 핸드오프, continuation prompt, or 이어서 작업할 프롬프트. Captures verified repo state, changed files, validation, pitfalls, risks, and one next step.
---

# New Session Handoff

## Purpose

Prepare or resume a fresh coding-agent session without relying on prior chat history, hidden reasoning, tool output, or compacted context.

This skill must not run interactive session commands such as Codex `/new`, control an agent CLI, or rotate sessions. In create mode, it writes handoff artifacts only and must not modify application code.

Create mode is read-mostly. It may write `HANDOFF.md`, `NEW_SESSION_PROMPT`, or focused handoff reference files only. It must not edit application code, run broad refactors, install dependencies, or start long-running commands.

## Core Policy

Recoverability first. Compactness second.

For small or medium tasks, prefer one compact `HANDOFF.md`.

For large tasks, use `HANDOFF.md` as an index plus focused handoff reference files, for example `handoffs/architecture.md`, `handoffs/changed-files.md`, `handoffs/validation.md`, `handoffs/pitfalls.md`, or another user-requested path.

Never compress away:

- verified decisions and rationale
- changed, created, deleted, or inspected files
- validation commands and results
- known risks, pitfalls, and failed approaches
- unresolved questions
- the smallest executable next step

A short handoff that loses critical recovery information is worse than a longer handoff with clear structure.

## Create Handoff

Use this mode when the user asks to make a handoff, says `핸드오프 만들어줘` or `핸드오프 문서 만들어줘`, save `HANDOFF.md`, prepare a new-session prompt, or preserve context before a new session.

1. Inspect current state before summarizing:
   - `pwd`
   - `git rev-parse --show-toplevel` if inside a Git repository
   - `git branch --show-current`
   - `git rev-parse --short HEAD`
   - `git status --short`
   - `git diff --stat`
   - relevant instruction files: `AGENTS.md`, `AGENTS.override.md`, `PLANS.md`, `PLAN.md`, `HANDOFF.md`, `CLAUDE.md`, `GEMINI.md`

2. Read enough files to verify the state.

3. Summarize only verified facts.
   - Do not invent file paths, commands, test results, branch names, or decisions.
   - Mark unknowns as `확인 필요` or `Unknown`.
   - Prefer exact paths and exact commands.
   - Keep log snippets short and include only lines needed to identify the result or failure.

4. Choose the size strategy:
   - Small or medium task: write one compact `HANDOFF.md`.
   - Large task: write `HANDOFF.md` as an index and create focused reference files. Each reference file must answer one recovery question, such as what architecture changed, what files changed, what validation ran, what failed, or what remains.
   - Do not create raw transcript dumps, long logs, or full diffs unless the user explicitly asks and they are essential for recovery.

5. Produce the requested artifact(s):
   - `NEW_SESSION_PROMPT`: a copy-paste prompt for a fresh agent session.
   - `HANDOFF.md`: a self-contained Markdown handoff or index handoff.
   - Optional focused reference files for large tasks.

6. Write only what the user requested:
   - If asked to create a handoff, write or update `HANDOFF.md` by default unless another path was requested.
   - If asked only for a prompt, do not write files; embed a self-contained Markdown handoff draft in the prompt instead of pointing to `HANDOFF.md`.

7. Make the handoff recoverable.
   - The next session must be able to continue from the repository state and the handoff artifacts alone.
   - If the handoff conflicts with the actual working tree, instruct the next session to trust the working tree.
   - Include the smallest safe first step, not only a broad to-do list.
   - If reference files are used, include a required reading order in `HANDOFF.md`.

8. End with markers for automation:

   ```text
   HANDOFF_READY: <absolute path or not-written>
   NEW_SESSION_PROMPT_READY: yes
   VALIDATION_RECORDED: yes|no
   SAFE_FOR_NEW_SESSION: yes|no
   ```

   Use `SAFE_FOR_NEW_SESSION: yes` only when all are true:
   - No command, build, test, dev server, or approval prompt is still running.
   - Current repo state was recorded: cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
   - Changed, created, deleted, or moved files are listed.
   - Validation command and result are recorded, or the reason validation was not run is explicit.
   - No unresolved user question blocks the next session.
   - The next step is singular and executable.

## Resume From Handoff

Use this mode when the user asks to continue from a handoff, read `HANDOFF.md`, or says `핸드오프 읽고 작업해줘`, `핸드오프 문서 읽고 작업해줘`, or `핸드오프 보고 이어서 작업`.

1. Establish context before implementing:
   - Confirm `pwd`, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
   - Read applicable instruction files and `HANDOFF.md`.
   - If `HANDOFF.md` contains a required reading order, read those focused reference files next.
   - Inspect files listed under `Files to inspect first`.

2. Compare `HANDOFF.md` with the actual working tree.
   - If they conflict, trust the working tree and report the mismatch.
   - Mark missing or uncertain handoff details as `확인 필요` or `Unknown`.

3. Report before editing:
   - Loaded instructions
   - Repo state
   - Handoff consistency
   - Reference files read, if any
   - Smallest next step

4. Continue from the smallest remaining task, following repository instructions and running the narrowest relevant validation after changes.

5. If the user asked only to inspect or resume context, stop after the report. If the user explicitly asked to continue implementation, proceed with only the smallest remaining task.

## Templates

Read the matching one-level reference before drafting each artifact:

- Read `references/handoff-template.md` when producing or updating `HANDOFF.md`.
- Read `references/new-session-prompt-template.txt` when producing `NEW_SESSION_PROMPT`.
- Read `references/quality-checklist.md` before setting `SAFE_FOR_NEW_SESSION: yes`.

## Automation Boundary

External agents such as Hermes or OpenClaw may use the final markers to decide when to send a session-reset command to an agent CLI PTY. This skill itself must not claim to execute `/new` or any other interactive reset command; it only prepares safe continuation artifacts.

---
name: new-session-handoff
description: Use when preparing a fresh coding-agent session after long work, context pressure, compaction, or orchestrated session rotation.
---

# New Session Handoff

## Purpose

Prepare a fresh coding-agent session to continue work without relying on prior chat history, hidden reasoning, tool output, or compacted context.

This skill creates handoff artifacts only. It must not run interactive session commands such as Codex `/new`, control an agent CLI, or rotate the session.

## Workflow

1. Inspect current state before summarizing:
   - `pwd`
   - `git rev-parse --show-toplevel` if inside a Git repository
   - `git branch --show-current`
   - `git status --short`
   - `git diff --stat`
   - relevant instruction files: `AGENTS.md`, `AGENTS.override.md`, `PLANS.md`, `PLAN.md`, `HANDOFF.md`, `CLAUDE.md`, `GEMINI.md`

2. Read enough files to verify the state. Do not modify application code.

3. Summarize only verified facts.
   - Do not invent file paths, commands, test results, branch names, or decisions.
   - Mark unknowns as `확인 필요` or `Unknown`.
   - Prefer exact paths and exact commands.
   - Keep log snippets short and include only lines needed to identify the result or failure.

4. Produce two artifacts:
   - `NEW_SESSION_PROMPT`: a copy-paste prompt for a fresh agent session.
   - `HANDOFF.md`: a self-contained Markdown handoff.

5. Write only what the user requested:
   - If asked to save the handoff, write or update `HANDOFF.md` unless another path was requested.
   - If asked only for a prompt, return the prompt and Markdown draft without writing files.

6. Make the handoff self-contained.
   - The next session must be able to continue from the repository state and the handoff alone.
   - If the handoff conflicts with the actual working tree, instruct the next session to trust the working tree.
   - Include the smallest safe first step, not only a broad to-do list.

7. End with markers for automation:

   ```text
   HANDOFF_READY: <absolute path or not-written>
   NEW_SESSION_PROMPT_READY: yes
   VALIDATION_RECORDED: yes|no
   SAFE_FOR_NEW_SESSION: yes|no
   ```

   Use `SAFE_FOR_NEW_SESSION: yes` only when no command is still running, the handoff is complete, and the current work can be resumed from the artifacts.

## Templates

Read the matching one-level reference before drafting each artifact:

- Read `references/handoff-template.md` when producing or updating `HANDOFF.md`.
- Read `references/new-session-prompt-template.txt` when producing `NEW_SESSION_PROMPT`.

## Automation Boundary

External agents such as Hermes or OpenClaw may use the final markers to decide when to send a session-reset command to an agent CLI PTY. This skill itself must not claim to execute `/new` or any other interactive reset command; it only prepares safe continuation artifacts.

## Quality Bar

- Focused: only solve session handoff, not general planning or CI repair.
- Progressive disclosure: keep the skill short; put platform-specific PTY automation outside the skill.
- Deterministic where possible: use exact commands and exact markers.
- Self-contained: the next worker should not need the previous conversation.

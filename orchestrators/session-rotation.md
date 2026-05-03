# Agent Session Rotation

This document is for an external PTY controller such as Hermes or OpenClaw. It describes when that controller may rotate an interactive coding-agent session.

It is not a Skill. The `new-session-handoff` skill prepares handoff artifacts; this workflow controls the interactive CLI.

## Responsibilities

- Skill `new-session-handoff`: inspect repository state, create `HANDOFF.md` or `NEW_SESSION_PROMPT`, and print readiness markers.
- External orchestrator: inspect the agent's status command, detect near-full context or compact events, wait for work completion, request handoff generation, send the agent-specific session-reset command, and inject the resume prompt.

## Rotation Flow

1. Monitor session health.
   - Send the agent-specific status command after task completion checkpoints or when context pressure is suspected.
   - For Codex CLI this may be `/status`.
   - Parse context usage if available.
   - Record whether automatic compacting has occurred if the CLI exposes that signal.

2. Do not rotate while work is active.
   - No shell command should be running.
   - The agent should not be mid-edit, mid-test, waiting on approval, or composing a final answer.
   - If uncertain, ask the agent for a short status instead of rotating.

3. Request a handoff.
   - Ask the active agent to use the `new-session-handoff` skill or equivalent handoff workflow.
   - Prefer saving `HANDOFF.md` when repository state will continue across sessions.
   - Require the final markers.

4. Check markers.

   ```text
   HANDOFF_READY: <absolute path or not-written>
   NEW_SESSION_PROMPT_READY: yes
   VALIDATION_RECORDED: yes|no
   SAFE_FOR_NEW_SESSION: yes
   ```

   If `SAFE_FOR_NEW_SESSION` is not `yes`, do not send a session-reset command.

5. Rotate.
   - Send the agent-specific session-reset command to the CLI PTY.
   - For Codex CLI this may be `/new`.
   - Wait for the new session prompt.
   - Inject a short resume prompt.

6. Resume.
   - The new session should read instruction files and `HANDOFF.md`.
   - It should verify handoff consistency against the working tree before editing.

## Suggested Resume Prompt

Use the canonical template at `skills/new-session-handoff/references/new-session-prompt-template.txt`. A short PTY-friendly version is:

```text
This is a continuation after a session rotation.

Read applicable instruction files and HANDOFF.md first. Confirm the working directory, Git root, branch, and git status. Compare HANDOFF.md with the actual working tree. If they conflict, prefer the working tree.

Then report:
1. Loaded instructions:
2. Repo state:
3. Handoff consistency:
4. First implementation step:

After that, continue from the smallest remaining task.
```

## Safe Rotation Conditions

- The previous session has completed or paused at a clean checkpoint.
- `HANDOFF.md` exists or the orchestrator captured `NEW_SESSION_PROMPT`.
- `git status --short` was recorded in the handoff.
- Last validation command and result were recorded, or the handoff explicitly says validation was not run.
- No command is running.
- No user approval prompt is open.
- No unresolved question blocks the next session.

## Unsafe Rotation Conditions

- Tests, builds, dev servers, or long-running commands are still active.
- Files were edited but the handoff does not list them.
- The prior agent is waiting for approval.
- The handoff contains unverified assumptions without marking them as `확인 필요` or `Unknown`.
- The orchestrator cannot find a readiness marker.

## Agent-Specific Notes

- Codex CLI: treat `/status` and `/new` as PTY inputs, not shell commands.
- Claude: use the equivalent Claude CLI status/context/session controls available in the user's environment; do not assume Codex slash commands exist.
- Gemini: use the equivalent Gemini CLI controls available in the user's environment; do not assume Codex slash commands exist.

## Notes for Hermes/OpenClaw

- Treat status and reset commands as PTY inputs, not shell commands.
- Keep a transcript snippet around the readiness markers for audit.
- Prefer a conservative threshold. Near-full context should trigger handoff preparation, not immediate rotation.
- If automatic compacting already occurred, rotate only after the current task reaches a clear checkpoint.

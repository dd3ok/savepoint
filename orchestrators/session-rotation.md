# Agent Session Rotation

This document is for an external PTY controller such as Hermes or OpenClaw. It describes when that controller may rotate an interactive coding-agent session.

It is not a Skill. The `savepoint` skill prepares savepoint artifacts; this workflow controls the interactive CLI.

## Responsibilities

- Skill `savepoint`: inspect repository state, create `.savepoint/SAVEPOINT.md` by default, optionally create focused detail artifacts as verified spillover, and print readiness markers.
- External orchestrator: inspect the agent's status command, detect near-full context or compact events, wait for work completion, request savepoint generation, send the agent-specific session-reset command, and inject the resume prompt.

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

3. Request a savepoint.
   - Ask the active agent to use the `savepoint` skill or equivalent savepoint workflow.
   - Prefer saving `.savepoint/SAVEPOINT.md` when repository state will continue across sessions.
   - Require the final markers.

4. Check the final marker block.

   Marker schema:

   ```text
   SAVEPOINT_V1
   SAVEPOINT_PATH: <absolute path or not-written>
   SAVEPOINT_MODE: lightweight|verified
   DETAILS_READY: yes|no|not-needed
   PROMPT_READY: yes|no
   DISK_RECORDED: yes|no
   VALIDATION_RECORDED: yes|no
   REDACTION_CHECKED: yes|no
   RESUME_READY: yes|no
   BLOCKERS: none|<short reason>
   END_SAVEPOINT_V1
   ```

   Parse only the final `SAVEPOINT_V1` block. Earlier drafts or quoted examples are not authoritative.

   Rotate only when `RESUME_READY` is `yes` and `BLOCKERS` is `none`. If `RESUME_READY` is not `yes`, do not send a session-reset command.

5. Rotate.
   - Send the agent-specific session-reset command to the CLI PTY.
   - For Codex CLI this may be `/new`.
   - Wait for the resume prompt.
   - Inject a short resume prompt.

6. Resume.
   - The resumed agent should read instruction files and the savepoint path recorded in `SAVEPOINT_PATH`.
   - If `DETAILS_READY: yes`, it should read only the detail artifacts required for the smallest next step.
   - It should verify savepoint consistency against the working tree before editing.

## Suggested Resume Prompt

Use the embedded `## Resume Prompt` from `SAVEPOINT.md` when possible. A short PTY-friendly fallback is:

```text
This is a continuation after a session rotation.

Read applicable instruction files and the savepoint recorded in SAVEPOINT_PATH first. Confirm the working directory, Git root, branch, short HEAD, git status, and diff stat. If SAVEPOINT.md lists detail artifacts, read only those needed for the smallest next step. Compare SAVEPOINT.md with the actual working tree. If they conflict, prefer the working tree.

Then report:
1. Loaded instructions:
2. Repo state:
3. Savepoint consistency:
4. Detail artifacts read:
5. First implementation step:

Continue only if RESUME_READY is yes and the user asked for implementation.
```

## Safe Rotation Conditions

- The previous session has completed or paused at a clean checkpoint.
- `SAVEPOINT.md` exists or the orchestrator captured an explicit lightweight savepoint response.
- cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat` were recorded in the savepoint.
- Dirty and staged files were recorded.
- Last validation command and result were recorded, or skipped validation has an explicit low-risk reason and next validation command.
- Secret redaction was checked.
- If detail spillover is used, every referenced detail artifact exists.
- No command is running.
- No user approval prompt is open.
- No unresolved question blocks the next session.

## Unsafe Rotation Conditions

- Tests, builds, dev servers, or long-running commands are still active.
- Files were edited but the savepoint does not list them.
- Detail spillover references missing artifacts.
- The prior agent is waiting for approval.
- The savepoint contains unverified assumptions without marking them as `확인 필요` or `Unknown`.
- The savepoint contains unredacted secrets, credentials, cookies, private keys, or full environment values.
- The orchestrator cannot find a readiness marker.

## Agent-Specific Notes

- Codex CLI: treat `/status` and `/new` as PTY inputs, not shell commands.
- Claude: use the equivalent Claude CLI status/context/session controls available in the user's environment; do not assume Codex slash commands exist.
- Gemini: use the equivalent Gemini CLI controls available in the user's environment; do not assume Codex slash commands exist.

## Notes for Hermes/OpenClaw

- Treat status and reset commands as PTY inputs, not shell commands.
- Keep a transcript snippet around the readiness markers for audit.
- Prefer a conservative threshold. Near-full context should trigger savepoint preparation, not immediate rotation.
- If automatic compacting already occurred, rotate only after the current task reaches a clear checkpoint.
- `RESUME_READY: yes` means the next session can reconstruct state and continue; it does not mean the code is correct.

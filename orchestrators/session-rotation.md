# Agent Session Rotation

This document is for an external PTY controller such as Hermes or OpenClaw. It describes when that controller may rotate an interactive coding-agent session.

It is not a Skill. The `new-session-handoff` skill prepares handoff artifacts; this workflow controls the interactive CLI.

## Responsibilities

- Skill `new-session-handoff`: inspect repository state, create `.new-session-handoff/HANDOFF.md` by default, optionally create focused detail artifacts in expanded mode, and print readiness markers.
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
   - Prefer saving `.new-session-handoff/HANDOFF.md` when repository state will continue across sessions.
   - Require the final markers.

4. Check the final marker block.

   Marker schema:

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

   Parse only the final `HANDOFF_AUTOMATION_V1` block. Earlier drafts or quoted examples are not authoritative.

   Rotate only when `SAFE_FOR_NEW_SESSION` is `yes` and `BLOCKERS` is `none`. If `SAFE_FOR_NEW_SESSION` is not `yes`, do not send a session-reset command.

5. Rotate.
   - Send the agent-specific session-reset command to the CLI PTY.
   - For Codex CLI this may be `/new`.
   - Wait for the new session prompt.
   - Inject a short resume prompt.

6. Resume.
   - The new session should read instruction files and the handoff path recorded in `HANDOFF_READY`.
   - If `HANDOFF_MODE: expanded`, it should read only the detail artifacts required for the smallest next step.
   - It should verify handoff consistency against the working tree before editing.

## Suggested Resume Prompt

Use the embedded `## Resume Prompt` from `HANDOFF.md` when possible. A short PTY-friendly fallback is:

```text
This is a continuation after a session rotation.

Read applicable instruction files and the handoff recorded in HANDOFF_READY first. Confirm the working directory, Git root, branch, short HEAD, git status, and diff stat. If HANDOFF.md lists detail artifacts, read only those needed for the smallest next step. Compare HANDOFF.md with the actual working tree. If they conflict, prefer the working tree.

Then report:
1. Loaded instructions:
2. Repo state:
3. Handoff consistency:
4. Detail artifacts read:
5. First implementation step:

Continue only if SAFE_FOR_NEW_SESSION is yes and the user asked for implementation.
```

## Safe Rotation Conditions

- The previous session has completed or paused at a clean checkpoint.
- `HANDOFF.md` exists or the orchestrator captured an explicit prompt-only handoff.
- cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat` were recorded in the handoff.
- Dirty and staged files were recorded.
- Last validation command and result were recorded, or skipped validation has an explicit low-risk reason and next validation command.
- Secret redaction was checked.
- If expanded mode is used, every referenced detail artifact exists.
- No command is running.
- No user approval prompt is open.
- No unresolved question blocks the next session.

## Unsafe Rotation Conditions

- Tests, builds, dev servers, or long-running commands are still active.
- Files were edited but the handoff does not list them.
- Expanded mode references missing detail artifacts.
- The prior agent is waiting for approval.
- The handoff contains unverified assumptions without marking them as `확인 필요` or `Unknown`.
- The handoff contains unredacted secrets, credentials, cookies, private keys, or full environment values.
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
- `SAFE_FOR_NEW_SESSION: yes` means the next session can reconstruct state and continue; it does not mean the code is correct.

# Agent Session Continuity

Portable session-continuity assets for long coding-agent tasks.

This repository is source material for humans and other repositories. It does not install anything on the current machine by itself.

## Contents

- `skills/new-session-handoff/`: a portable `SKILL.md` for creating self-contained handoff artifacts.
- `.agents/skills/new-session-handoff`: optional Codex-compatible project-skill entrypoint, symlinked to `skills/new-session-handoff/`.
- `.claude/skills/new-session-handoff`: optional Claude Code project-skill entrypoint, symlinked to `skills/new-session-handoff/`.
- `orchestrators/session-rotation.md`: guidance for PTY controllers such as Hermes or OpenClaw.
- `examples/`: filled handoff and resume prompt examples.

## Intended Use

`skills/new-session-handoff/` is the canonical source. Copy, vendor, or symlink it into the skill location used by your agent environment.

The `.agents/skills/...` and `.claude/skills/...` symlinks are not required for the repository to be useful. Keep them only when you want project-level automatic skill discovery in compatible tools.

Common locations include:

- Codex personal skills: `$HOME/.agents/skills/new-session-handoff/`
- Codex repo skills: `<repo>/.agents/skills/new-session-handoff/`
- Claude personal skills: `$HOME/.claude/skills/new-session-handoff/`
- Claude project skills: `<repo>/.claude/skills/new-session-handoff/`

For Claude, Gemini, or other agents, keep the same core workflow and adjust only the agent-specific installation path and session-control commands. If your tool uses a different skill discovery path, use that tool's path and keep `skills/new-session-handoff/` as the source of truth.

## Boundary

The skill prepares:

- `HANDOFF.md`
- `NEW_SESSION_PROMPT`
- readiness markers such as `SAFE_FOR_NEW_SESSION`

The skill does not execute interactive reset commands. Hermes, OpenClaw, or another PTY controller should own status checks, context thresholds, and session rotation.

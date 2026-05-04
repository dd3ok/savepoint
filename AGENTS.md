# Repository Instructions

This repository contains session-continuity assets for coding agents such as Codex, Claude, Gemini, and external PTY orchestrators.

## Structure

- `skills/new-session-handoff/`: portable skill that creates handoff artifacts.
- `orchestrators/`: External PTY-controller guidance for Hermes/OpenClaw style agents.
- `examples/`: Minimal examples and prompt templates.

## Rules

- Keep the skill focused on session handoff artifacts and safe continuation from `HANDOFF.md`.
- Keep `/status`, `/new`, PTY control, and context-threshold policy outside the skill.
- Do not claim a skill can execute interactive slash commands.
- Use exact command names, exact markers, and conservative safety checks.
- Prefer concise files over broad documentation.

## Validation

Before committing changes to this repository, run:

```bash
python3 scripts/check-frontmatter.py
python3 scripts/check-marker-block.py
python3 scripts/check-marker-semantics.py
python3 scripts/validate-examples.py
python3 scripts/validate-repo.py
```

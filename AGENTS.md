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

## Mandatory Skill Usage

- Use `$new-session-handoff` when the user asks to create, update, inspect, or resume `.new-session-handoff/HANDOFF.md`, a new-session continuation prompt, or Korean equivalents such as `핸드오프 만들어줘` / `핸드오프 읽고 이어서 해줘`.
- Do not use this skill for ordinary summaries, README writing, AGENTS.md authoring alone, code implementation, `/new`, `/status`, PTY control, or session-rotation policy.
- When updating the skill contract, template, marker semantics, examples, or evals, run the validation commands below before committing.

## Validation

Before committing changes to this repository, run:

```bash
python3 scripts/check-frontmatter.py
python3 scripts/check-marker-block.py
python3 scripts/check-marker-semantics.py
python3 scripts/validate-examples.py
python3 scripts/validate-repo.py
```

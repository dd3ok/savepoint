# Repository Instructions

This repository contains session-continuity assets for coding agents such as Codex, Claude, Gemini, and external PTY orchestrators.

## Structure

- `skills/savepoint/`: portable skill that creates savepoint artifacts.
- `orchestrators/`: External PTY-controller guidance for Hermes/OpenClaw style agents.
- `examples/`: Minimal examples and prompt templates.

## Rules

- Keep the skill focused on session savepoint artifacts and safe continuation from `SAVEPOINT.md`.
- Keep `/status`, `/new`, PTY control, and context-threshold policy outside the skill.
- Do not claim a skill can execute interactive slash commands.
- Use exact command names, exact markers, and conservative safety checks.
- Prefer concise files over broad documentation.

## Mandatory Skill Usage

- Use `$savepoint` when the user asks to create, update, load, inspect, or resume `.savepoint/SAVEPOINT.md`, a text/copy-paste savepoint, or Korean equivalents such as `세이브포인트 만들어줘` / `세이브포인트 로드해줘` / `세이브포인트 읽어줘` / `세이브포인트 이어서 해줘`.
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
python3 scripts/check-install-helper.py
python3 scripts/validate_savepoint.py --allow-example-paths examples/SAVEPOINT.filled.example.md examples/file-bugfix/SAVEPOINT.md examples/file-architecture/SAVEPOINT.md examples/unsafe-savepoint/SAVEPOINT.md
git diff --check
```

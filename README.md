# Agent Session Handoff Skill

Portable session-continuity assets for coding agents such as Codex, Claude, Gemini, and external PTY orchestrators.

`new-session-handoff` creates or resumes a verified `HANDOFF.md` for moving long coding-agent work into a fresh session. The handoff is a recoverable entry manifest, not a raw transcript and not a claim that the code is correct.

## TL;DR

- `HANDOFF.md` records verified repo state, changed files, validation status, risks, and one executable next step.
- Large work can use focused `details/*.md` artifacts while keeping `HANDOFF.md` as the landing page.
- `NEW_SESSION_PROMPT.txt` gives the next agent a copy-paste continuation prompt.
- `HANDOFF_AUTOMATION_V1` markers let external orchestrators decide whether session rotation is safe.
- The skill never runs `/new`, `/status`, controls PTYs, or edits application code while creating a handoff.

## Canonical Contract

Runtime behavior is intentionally concentrated in the distributed skill:

- Skill router: `skills/new-session-handoff/SKILL.md`
- Artifact contract: `skills/new-session-handoff/references/handoff-contract.md`
- Handoff skeleton: `skills/new-session-handoff/references/handoff-template.md`
- Prompt template: `skills/new-session-handoff/references/new-session-prompt-template.txt`
- Marker schema: `skills/new-session-handoff/schemas/handoff-automation-v1.schema.json`
- Portable validator: `skills/new-session-handoff/scripts/validate_handoff.py`

README is a map. The contract files above are the source of truth for marker semantics, `SAFE_FOR_NEW_SESSION`, trust order, expanded artifacts, and resume behavior.

## Repository Layout

```text
.
├── README.md
├── SECURITY.md
├── CHANGELOG.md
├── AGENTS.md
├── skills/
│   └── new-session-handoff/
│       ├── SKILL.md
│       ├── LICENSE.txt
│       ├── agents/openai.yaml
│       ├── references/
│       │   ├── handoff-contract.md
│       │   ├── handoff-template.md
│       │   ├── new-session-prompt-template.txt
│       │   └── detail-*-template.md
│       ├── schemas/handoff-automation-v1.schema.json
│       └── scripts/
│           ├── handoff_contract.py
│           └── validate_handoff.py
├── examples/
├── evals/
├── orchestrators/
└── scripts/
```

`skills/new-session-handoff/` is the portable skill package. The root-level `examples/`, `evals/`, `orchestrators/`, and `scripts/validate-repo.py` are maintainer assets. The root `scripts/validate_handoff.py` is a compatibility wrapper around the portable validator.

## Installation / Vendoring

Copy, vendor, or symlink the canonical skill into the location used by your agent environment.

Common locations:

- Codex personal skills: `$HOME/.agents/skills/new-session-handoff/`
- Codex repo skills: `<repo>/.agents/skills/new-session-handoff/`
- Claude personal skills: `$HOME/.claude/skills/new-session-handoff/`
- Claude project skills: `<repo>/.claude/skills/new-session-handoff/`

Example project symlinks:

```bash
mkdir -p .agents/skills .claude/skills
ln -s ../../skills/new-session-handoff .agents/skills/new-session-handoff
ln -s ../../skills/new-session-handoff .claude/skills/new-session-handoff
```

## Examples

- `examples/compact-bugfix/`: compact handoff for a small bug fix.
- `examples/expanded-architecture/`: expanded handoff with focused detail artifacts.
- `examples/unsafe-handoff/`: intentionally unsafe handoff showing why `SAFE_FOR_NEW_SESSION: no` matters.
- `examples/resume-prompt.example.txt`: prompt for continuing from a handoff.

Examples are maintainer/demo material. They are not required in the distributed skill package.

## Evals

`evals/` contains lightweight manual scenarios for maintaining the skill contract. Use them when changing `SKILL.md`, templates, marker semantics, examples, validators, or orchestrator guidance.

Core expectations:

- create mode does not modify application code.
- generated artifacts contain verified facts or explicit unknowns.
- resume mode verifies disk state before coding.
- expanded mode uses focused detail artifacts instead of context dumps.
- unsafe states do not emit `SAFE_FOR_NEW_SESSION: yes`.
- secrets are redacted or omitted.

## Validation

Before committing changes, run:

```bash
python3 scripts/check-frontmatter.py
python3 scripts/check-marker-block.py
python3 scripts/check-marker-semantics.py
python3 scripts/validate-examples.py
python3 scripts/validate-repo.py
```

To validate generated handoff artifacts directly:

```bash
python3 scripts/validate_handoff.py HANDOFF.md
```

The root validator command delegates to the portable validator inside `skills/new-session-handoff/scripts/`.

## Orchestrators

External PTY controllers can read the final marker block and decide whether to rotate a session. See `orchestrators/session-rotation.md`.

This skill prepares and consumes handoff artifacts only. Session reset commands, context-threshold policy, PTY input, and agent CLI orchestration stay outside the skill.

## Versioning

The current handoff schema is:

```text
HANDOFF_SCHEMA_VERSION: 1
```

Breaking changes to marker names, required sections, marker meanings, or detail path resolution should increment the schema version and update examples, evals, README, validators, and orchestrator guidance together.

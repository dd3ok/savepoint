# Savepoint Skill

`savepoint` is a text/file checkpoint skill for coding agents such as Codex and Claude. It helps hand off full-context coding sessions, preserve repo/Git state, and safely resume from `.savepoint/SAVEPOINT.md` without relying on prior chat context.

[한국어 README](README.ko.md)

It provides one skill, `$savepoint`, with three user-facing workflows:

| Need | Say | Output |
|---|---|---|
| File Savepoint | `Create a savepoint`, `Create a savepoint file`, `Create SAVEPOINT.md` | `.savepoint/SAVEPOINT.md` |
| Load / Resume Savepoint | `Load the savepoint`, `Read the savepoint`, `Resume from the savepoint`, `Resume from SAVEPOINT.md` | Verify/report state; continue only if requested and safe |
| Text Savepoint | `Create a text savepoint`, `Create a copy-paste savepoint`, `Create a savepoint without writing files` | Response text |

Default to **File Savepoint** when preserving coding-session state. Default to **Load / Resume Savepoint** when continuing from an existing `.savepoint/SAVEPOINT.md`.

Use **Text Savepoint** only for explicit copy-paste, text, or no-file requests that do not need file recovery guarantees.

This skill is not a generic conversation summarizer. It does not run `/new`, `/status`, control PTYs, rotate sessions, choose context thresholds, or edit application code while creating a savepoint.

## Use Cases

- Resume a coding-agent session after the context window is full.
- Hand off repo/Git state from one Codex or Claude session to another.
- Create a copy-paste Text Savepoint for a quick one-off transfer.

## Why Savepoint

Savepoint turns open-ended discovery, inference, and retry work from free-form handoffs into a short, structured check of Git/disk state and savepoint consistency.

## Default Artifact

File savepoints write:

```text
.savepoint/SAVEPOINT.md
```

File `SAVEPOINT.md` embeds `## Resume Prompt` and ends with a `SAVEPOINT_V1` marker block. The exact field schema lives in `skills/savepoint/schemas/savepoint-v1.schema.json`; marker semantics live in `skills/savepoint/references/savepoint-contract.md`.

## Canonical Contract

The canonical files are:

- Skill router: `skills/savepoint/SKILL.md`
- Artifact contract: `skills/savepoint/references/savepoint-contract.md`
- Savepoint skeleton: `skills/savepoint/references/savepoint-template.md`
- Token-efficient draft helper: `skills/savepoint/scripts/create_savepoint_stub.py`
- Context packaging: `skills/savepoint/references/context-packaging.md`
- Marker schema: `skills/savepoint/schemas/savepoint-v1.schema.json`
- Portable validator: `skills/savepoint/scripts/validate_savepoint.py`

The root-level `examples/`, `evals/`, `orchestrators/`, and `scripts/validate-repo.py` are maintainer assets. The root `scripts/validate_savepoint.py` forwards to the portable validator.

## Repository Layout

```text
.
├── README.md
├── README.ko.md
├── SECURITY.md
├── AGENTS.md
├── skills/
│   └── savepoint/
│       ├── SKILL.md
│       ├── LICENSE.txt
│       ├── agents/openai.yaml
│       ├── references/
│       │   ├── context-packaging.md
│       │   ├── savepoint-contract.md
│       │   └── savepoint-template.md
│       ├── schemas/savepoint-v1.schema.json
│       └── scripts/
│           ├── create_savepoint_stub.py
│           ├── savepoint_contract.py
│           └── validate_savepoint.py
├── examples/
├── evals/
├── orchestrators/
└── scripts/
```

## Installation

Typical skill locations:

- Codex user skill: `$HOME/.agents/skills/savepoint/`
- Codex repo skill: `<repo>/.agents/skills/savepoint/`
- Claude user skill: `$HOME/.claude/skills/savepoint/`
- Claude project skill: `<repo>/.claude/skills/savepoint/`

Repo symlink example:

```bash
mkdir -p .agents/skills .claude/skills
ln -s ../../skills/savepoint .agents/skills/savepoint
ln -s ../../skills/savepoint .claude/skills/savepoint
```

Safe install helper:

```bash
python3 scripts/install.py --target claude --scope user
python3 scripts/install.py --target codex --scope repo --apply --add-gitignore
```

The helper defaults to dry-run. It writes files only with `--apply`; `--add-gitignore` is repo-scope only and appends `.savepoint/`.

## Examples

- `examples/file-bugfix/`: small file savepoint.
- `examples/file-architecture/`: file savepoint with focused `details/*.md` spillover.
- `examples/text-note/`: response-only text savepoint note.
- `examples/unsafe-savepoint/`: intentionally unsafe file savepoint with `RESUME_READY: no`.

## Evals

`evals/trigger-queries.json` records should-trigger and should-not-trigger prompts, including SQL/database `SAVEPOINT` near misses.

Core expectations:

- Text output is short and does not claim repo recovery.
- File output writes `.savepoint/SAVEPOINT.md`.
- File output embeds `## Resume Prompt`.
- Large file savepoints use focused detail artifacts instead of bloating `SAVEPOINT.md`.
- Load/resume verifies disk state before continuation or implementation.
- Disk state wins over savepoint text.
- Secrets are redacted.
- File `SAVEPOINT_V1` marker block is present and honest.
- Unsafe state never emits `RESUME_READY: yes`.

## Validation

Before committing changes to this repository, run:

```bash
python3 scripts/check-frontmatter.py
python3 scripts/check-marker-block.py
python3 scripts/check-marker-semantics.py
python3 scripts/validate-examples.py
python3 scripts/validate-repo.py
python3 scripts/check-savepoint-stub.py
python3 scripts/check-install-helper.py
python3 scripts/validate_savepoint.py --allow-example-paths examples/SAVEPOINT.filled.example.md examples/file-bugfix/SAVEPOINT.md examples/file-architecture/SAVEPOINT.md examples/unsafe-savepoint/SAVEPOINT.md
git diff --check
```

To validate a generated file savepoint:

```bash
python3 scripts/validate_savepoint.py .savepoint/SAVEPOINT.md
```

## Orchestrators

External PTY controllers may parse the final `SAVEPOINT_V1` block and decide whether to rotate sessions. This skill only prepares file artifacts or text notes; orchestration remains outside the skill.

See `orchestrators/session-rotation.md`.

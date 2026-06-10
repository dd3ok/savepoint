# Savepoint Skill

`savepoint` helps coding agents preserve continuation state for a later session.

A savepoint is a handoff-style checkpoint for when a coding agent's context is full and a new session needs to continue from saved repo state; canonical commands and files use `savepoint` and `.savepoint/SAVEPOINT.md`.

[한국어 README](README.ko.md)

It provides one skill, `$savepoint`, with three user-facing workflows:

| Need | Say | Output |
|---|---|---|
| File Savepoint | `Create a savepoint`, `Create a savepoint file`, `Create SAVEPOINT.md` | `.savepoint/SAVEPOINT.md` |
| Text Savepoint | `Create a copy-paste text savepoint`, `Create a no-file text savepoint` | Response text |
| Load / Resume Savepoint | `Load the savepoint`, `Read the savepoint`, `Resume from the savepoint`, `Resume from SAVEPOINT.md` | Verify/report state; continue only if requested and safe |

Use **File Savepoint** by default when preserving coding-session state, and use **Load / Resume Savepoint** by default when starting from an existing `.savepoint/SAVEPOINT.md`.

Use **Text Savepoint** for one-off or simple copy-paste transfer only when you explicitly do not need a file or repo recovery guarantees.

Use **Load / Resume Savepoint** when a fresh coding agent must read `.savepoint/SAVEPOINT.md`, compare it with current disk/Git state, and continue only if requested and safe.

This skill is not a generic conversation summarizer. It does not run `/new`, `/status`, control PTYs, rotate sessions, choose context thresholds, or edit application code while creating a savepoint.

## Default Artifact

File savepoints write:

```text
.savepoint/SAVEPOINT.md
```

File `SAVEPOINT.md` embeds `## Resume Prompt` and ends with a `SAVEPOINT_V1` marker block. The exact field schema lives in `skills/savepoint/schemas/savepoint-v1.schema.json`; marker semantics live in `skills/savepoint/references/savepoint-contract.md`.

## Usage

```text
Create a savepoint.
```

Creates a File Savepoint at `.savepoint/SAVEPOINT.md`.

```text
Load the savepoint.
Resume from SAVEPOINT.md.
```

Reads the file savepoint, verifies current disk/Git state, reports consistency or drift, and continues only when safe and explicitly requested.

```text
Create a copy-paste text savepoint.
```

Creates a Text Savepoint for one-off or simple transfer without file recovery guarantees.

## Canonical Contract

The canonical files are:

- Skill router: `skills/savepoint/SKILL.md`
- Artifact contract: `skills/savepoint/references/savepoint-contract.md`
- Savepoint skeleton: `skills/savepoint/references/savepoint-template.md`
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

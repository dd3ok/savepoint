# Savepoint

A continue/load system for coding agents.

Savepoint helps a fresh agent session load the current coding run without relying on prior chat context.

## Prompts

| Prompt | Meaning |
|---|---|
| `/savepoint save` | Create or refresh `.savepoint/SAVEPOINT.md`. |
| `/savepoint load` | Load and verify an existing Savepoint. Continue only if requested and safe. |
| `/savepoint text` | Produce a response-only copy-paste handoff. No file, no recovery guarantee. |

Native slash-command support depends on the client. If a client does not pass custom slash prompts through to the model, use the natural-language equivalent: `Use $savepoint to save`, `Use $savepoint to load`, or `Use $savepoint to create a text handoff`.

[한국어 README](README.ko.md)

The file-backed Savepoint path is the default for preserving coding-session state, repo/Git state, validation, redaction, or safe resume. Use `/savepoint load` when continuing from an existing `.savepoint/SAVEPOINT.md`.

Use `/savepoint text` only for explicit copy-paste, text, or no-file requests that do not need file recovery guarantees.

## Use Cases

- Resume a coding-agent session after the context window is full.
- Recover coding state after automatic context compaction or before an intentional session reset.
- Transfer repo/Git state from one Codex or Claude session to another.
- Create a `/savepoint text` copy-paste handoff for a quick one-off transfer.

For short one-off summaries, a plain summary may be cheaper; use savepoint when structured coding transfer or recovery matters.

## Why Savepoint

Savepoint turns open-ended discovery, inference, and retry work from free-form transfer notes into a short, structured check of Git/disk state and savepoint consistency.

## Savepoint Artifact

Savepoints write:

```text
.savepoint/SAVEPOINT.md
```

`SAVEPOINT.md` embeds `## Resume Prompt` and ends with a `SAVEPOINT_V1` marker block. The field schema lives in `skills/savepoint/schemas/savepoint-v1.schema.json`; marker semantics live in `docs/reference/savepoint-contract.md`.

## Runtime Boundary

Normal create/load uses:

- Skill router: `skills/savepoint/SKILL.md`
- Renderer/finalizer: `skills/savepoint/scripts/render_savepoint.py`
- Portable validator: `skills/savepoint/scripts/validate_savepoint.py`
- Shared marker/snapshot helpers: `skills/savepoint/scripts/savepoint_contract.py`
- Marker schema: `skills/savepoint/schemas/savepoint-v1.schema.json`

Reference docs, templates, examples, evals, orchestrators, and `scripts/validate-repo.py` are maintainer/debug assets, not normal agent context. The root `scripts/validate_savepoint.py` and `scripts/render_savepoint.py` forward to the portable runtime tools.

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
│       ├── schemas/savepoint-v1.schema.json
│       └── scripts/
│           ├── render_savepoint.py
│           ├── savepoint_contract.py
│           └── validate_savepoint.py
├── docs/
│   └── reference/
│       ├── context-packaging.md
│       ├── savepoint-contract.md
│       └── savepoint-template.md
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

- `examples/file-bugfix/`: small Savepoint.
- `examples/file-architecture/`: Savepoint with focused `details/*.md` spillover.
- `examples/text-note/`: response-only `/savepoint text` note.
- `examples/unsafe-savepoint/`: intentionally unsafe Savepoint with `RESUME_READY: no`.

## Maintainer Evals

`evals/trigger-queries.json` records should-trigger and should-not-trigger prompts, including SQL/database `SAVEPOINT` near misses.

Core expectations:

- `/savepoint text` output is short and does not claim repo recovery.
- Savepoint output writes `.savepoint/SAVEPOINT.md`.
- Savepoint output embeds `## Resume Prompt`.
- Large Savepoints use focused detail artifacts instead of bloating `SAVEPOINT.md`.
- Load/resume verifies disk state before continuation or implementation.
- Disk state wins over savepoint text.
- Secrets are redacted.
- `SAVEPOINT_V1` marker block is present and honest.
- Unsafe state never emits `RESUME_READY: yes`.

## Maintainer Validation

Use `scripts/validate_savepoint.py` for generated Savepoint artifacts. It validates a `SAVEPOINT.md` file and is the portable runtime check.

Use `scripts/validate-repo.py` only for maintaining this repository. It checks packaging, examples, trigger evals, and marker/schema contracts.

Before committing repository changes, run:

```bash
python3 scripts/check-frontmatter.py
python3 scripts/check-marker-block.py
python3 scripts/check-marker-semantics.py
python3 scripts/validate-examples.py
python3 scripts/validate-repo.py
python3 scripts/check-savepoint-renderer.py
python3 scripts/check-install-helper.py
python3 scripts/validate_savepoint.py --allow-example-paths examples/SAVEPOINT.filled.example.md examples/file-bugfix/SAVEPOINT.md examples/file-architecture/SAVEPOINT.md examples/unsafe-savepoint/SAVEPOINT.md
git diff --check
```

To validate a generated Savepoint:

```bash
python3 scripts/validate_savepoint.py .savepoint/SAVEPOINT.md
```

## Orchestrators

External PTY controllers may parse the final `SAVEPOINT_V1` block and decide whether to rotate sessions. This skill only prepares file artifacts or text notes; orchestration remains outside the skill.

See `orchestrators/session-rotation.md`.

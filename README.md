# Savepoint Skill

`savepoint` helps coding agents preserve continuation state for a later session.

It provides one skill, `$savepoint`, with two user-facing paths:

| Need | Say | Output |
|---|---|---|
| Lightweight transfer | `간단 세이브포인트 만들어줘`, `3000자 이내로 인계 요약해줘` | Response text by default |
| Verified recovery | `SAVEPOINT.md 만들어줘`, `repo/Git 상태 포함해서 세이브포인트 만들어줘` | `.savepoint/SAVEPOINT.md` |
| Legacy wording | `HANDOFF.md 만들어줘`, `핸드오프 읽고 이어서 해줘` | Routes to Savepoint; new verified artifacts use `.savepoint/SAVEPOINT.md` |

Use **Lightweight** when you want the lowest token/tool cost and do not need repo recovery guarantees.

Use **Verified** when a fresh coding agent must reconstruct current disk/Git state without prior chat history. Verified savepoints record changed files, validation status, risks, relevant instruction/state files, and one narrow next action.

This skill is not a generic conversation summarizer. It does not run `/new`, `/status`, control PTYs, rotate sessions, choose context thresholds, or edit application code while creating a savepoint.

## Default Artifact

Verified savepoints write:

```text
.savepoint/SAVEPOINT.md
```

Verified `SAVEPOINT.md` embeds `## Resume Prompt` and ends with a `SAVEPOINT_V1` marker block. The exact field schema lives in `skills/savepoint/schemas/savepoint-v1.schema.json`; marker semantics live in `skills/savepoint/references/savepoint-contract.md`.

`handoff`, `HANDOFF.md`, and `핸드오프` are accepted as legacy aliases for routing, but the canonical artifact remains `.savepoint/SAVEPOINT.md`.

## Korean Usage

```text
간단 세이브포인트 만들어줘. 다음 세션은 PR 리뷰만 하면 돼.
```

Creates a Lightweight note. It must not claim `RESUME_READY: yes`.
By default it does not emit a marker block.

```text
새 세션에서 안전하게 이어갈 SAVEPOINT.md 만들어줘. 현재 git 상태와 validation 결과 포함해줘.
```

Creates a Verified savepoint at `.savepoint/SAVEPOINT.md`.

```text
세이브포인트 읽고 현재 repo 상태 확인한 다음 이어서 작업해줘.
```

Reads the savepoint, compares it with current disk/Git state, reports consistency or drift, and continues only when safe and explicitly requested.

## Canonical Contract

The canonical files are:

- Skill router: `skills/savepoint/SKILL.md`
- Artifact contract: `skills/savepoint/references/savepoint-contract.md`
- Savepoint skeleton: `skills/savepoint/references/savepoint-template.md`
- Context packaging: `skills/savepoint/references/context-packaging.md`
- Marker schema: `skills/savepoint/schemas/savepoint-v1.schema.json`
- Portable validator: `skills/savepoint/scripts/validate_savepoint.py`

The root-level `examples/`, `evals/`, `orchestrators/`, and `scripts/validate-repo.py` are maintainer assets. The root `scripts/validate_savepoint.py` is a compatibility wrapper around the portable validator.

## Repository Layout

```text
.
├── README.md
├── SECURITY.md
├── CHANGELOG.md
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

- `examples/verified-bugfix/`: small verified savepoint.
- `examples/verified-architecture/`: verified savepoint with focused `details/*.md` spillover.
- `examples/lightweight-note/`: response-only lightweight savepoint note.
- `examples/unsafe-savepoint/`: intentionally unsafe savepoint with `RESUME_READY: no`.

## Evals

`evals/trigger-queries.json` records should-trigger and should-not-trigger prompts, including SQL/database `SAVEPOINT` near misses.

Core expectations:

- Lightweight output is short and does not claim repo recovery.
- Verified output writes `.savepoint/SAVEPOINT.md`.
- Verified output embeds `## Resume Prompt`.
- Large verified work uses focused detail artifacts instead of bloating `SAVEPOINT.md`.
- Resume verifies disk state before implementation.
- Disk state wins over savepoint text.
- Secrets are redacted.
- Verified `SAVEPOINT_V1` marker block is present and honest.
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
python3 scripts/validate_savepoint.py --allow-example-paths examples/SAVEPOINT.filled.example.md examples/verified-bugfix/SAVEPOINT.md examples/verified-architecture/SAVEPOINT.md examples/unsafe-savepoint/SAVEPOINT.md
git diff --check
```

To validate a generated verified savepoint:

```bash
python3 scripts/validate_savepoint.py .savepoint/SAVEPOINT.md
```

## Orchestrators

External PTY controllers may parse the final `SAVEPOINT_V1` block and decide whether to rotate sessions. This skill only prepares artifacts or lightweight notes; orchestration remains outside the skill.

See `orchestrators/session-rotation.md`.

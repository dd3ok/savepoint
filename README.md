# Agent Session Handoff Skill

긴 코딩 에이전트 작업을 새 세션으로 안전하게 넘기기 위한 portable skill, templates, examples, automation markers 모음입니다.

이 저장소는 사람과 다른 저장소가 가져다 쓸 source material입니다. 현재 머신에 무언가를 직접 설치하지 않습니다.

## 한국어 요약

`new-session-handoff`는 Codex, Claude Code, Gemini 같은 코딩 에이전트가 긴 작업을 새 세션으로 넘길 때 쓰는 검증된 handoff 스킬입니다.

핵심 산출물은 `HANDOFF.md`입니다. `HANDOFF.md`는 이전 대화 전체를 덤프한 transcript도 아니고, 모든 내용을 억지로 100줄 안에 압축한 요약문도 아닙니다. 새 세션이 무엇을 확인하고 어디부터 읽어야 하는지 알려주는 **복구 가능한 entry manifest**입니다.

큰 아키텍처 변경이나 대규모 파일 수정은 `HANDOFF.md` 안에 전부 넣지 않습니다. `details/architecture.md`, `details/changed-files.md`, `details/validation.md`, `details/pitfalls.md` 같은 focused detail artifacts로 분리하고, 새 세션은 필요한 detail만 선택적으로 읽습니다.

새 세션은 이전 대화나 숨은 추론에 의존하지 않습니다. `HANDOFF.md`, 필요한 `details/*.md`, 실제 working tree, 현재 instruction files를 확인한 뒤 가장 작은 다음 작업부터 이어갑니다.

## TL;DR

- `new-session-handoff` creates or resumes a verified coding-agent handoff.
- It writes a compact `HANDOFF.md` entry manifest, not a raw transcript.
- It records verified repository state, changed files, validation status, pitfalls, and one executable next step.
- It supports expanded handoffs for large architecture or multi-file work by linking focused `details/*.md` artifacts.
- It emits machine-readable readiness markers so an external orchestrator can decide whether a session is safe to rotate.

## Why This Exists

Long coding-agent sessions degrade when too much chat history, tool output, logs, and partial reasoning accumulate in one context window. Raw transcript dumps make the next session slow and noisy. Over-compressed summaries can drop the important "why" behind architecture decisions.

This skill creates a deterministic checkpoint instead:

1. inspect the real working tree,
2. record only verified recovery facts,
3. separate the compact manifest from optional details,
4. require the fresh session to verify disk state before coding.

The goal is recoverability, not completeness.

## What It Is

`new-session-handoff` creates or resumes a verified handoff for coding agents such as Codex, Claude Code, Gemini, and similar tools.

The central artifact is `HANDOFF.md`. It is not a transcript and not a forced 100-line full summary. It is a recoverable entry manifest: a fresh session reads it first, verifies the actual working tree, then continues from the smallest safe next step.

For complex work, `HANDOFF.md` points to focused detail artifacts such as architecture notes, changed-file ledgers, validation notes, pitfalls, or open questions. The manifest stays compact while important recovery context remains available on demand.

## Design Principles

1. Recoverability over completeness. Preserve the facts needed to continue safely; do not dump everything.
2. Verified facts over inferred summaries. If a fact was not inspected, mark it as `Unknown` or `확인 필요`.
3. Disk state wins over handoff text. On resume, the actual working tree is the source of truth.
4. Manifest first, details only when needed. Read `HANDOFF.md` first; read detail artifacts selectively.
5. Surgical continuation. Continue only the smallest remaining task before broad plans or refactors.
6. No session control inside the skill. The skill does not run `/new`, reset PTYs, force compaction, or rotate sessions.
7. No secret leakage. Redact secrets before writing any handoff artifact.

## Handoff Modes

| Mode | Use When | Output |
| --- | --- | --- |
| `compact` | Normal bugs, small features, narrow debugging | One `HANDOFF.md` with essential recovery details |
| `expanded` | Large architecture changes, many files, long validation history | `HANDOFF.md` plus focused `details/*.md` artifacts |
| `prompt-only` | File writes are not desired or not possible | A self-contained new-session prompt, no written artifacts |

### Compact Mode

Use `compact` when one manifest can preserve enough context without hiding important rationale, risks, or validation state.

### Expanded Mode

Use `expanded` when forcing everything into one short file would lose critical recovery information. `HANDOFF.md` remains the landing page. Detail artifacts answer focused recovery questions.

Recommended default layout:

```text
HANDOFF.md
details/
  architecture.md
  changed-files.md
  validation.md
  pitfalls.md
  open-questions.md
```

For durable stored handoff packages, use the same structure under a slugged directory:

```text
handoffs/<timestamp-or-slug>/HANDOFF.md
handoffs/<timestamp-or-slug>/details/architecture.md
handoffs/<timestamp-or-slug>/details/changed-files.md
handoffs/<timestamp-or-slug>/details/validation.md
handoffs/<timestamp-or-slug>/details/pitfalls.md
handoffs/<timestamp-or-slug>/details/open-questions.md
```

All detail paths are resolved relative to the directory containing `HANDOFF.md` unless the handoff explicitly says otherwise.

### Prompt-Only Mode

Use `prompt-only` when the user wants a copy-paste continuation prompt but does not want the agent to write files. The prompt must still include verified repo state, validation status, blockers, and the smallest next step.

## When To Use

- Context is nearly full or compaction happened.
- A long task needs to move to a new Codex, Claude, Gemini, or similar session.
- A user asks for `HANDOFF.md`, `NEW_SESSION_PROMPT`, `핸드오프`, or `이어서 작업할 프롬프트`.
- An external PTY orchestrator needs safe readiness markers before rotating a session.
- A team needs a reusable handoff format across repositories.

## When Not To Use

- The user is starting an unrelated new task.
- A tiny one-shot task has no session-transfer risk.
- Current repository state cannot be inspected.
- The necessary context contains secrets that cannot be safely redacted.
- The user is asking the skill to run `/new`, `/status`, reset a PTY, or control an interactive agent session.
- The next session would need broad authority that the user has not granted, such as dependency/API/DB/schema changes, destructive commands, force pushes, or large deletions.

## Workflow

### Create Handoff

Ask your agent:

```text
Use $new-session-handoff to create HANDOFF.md and a new-session prompt.
```

The skill should inspect the real repository state first:

- `pwd`
- Git root, branch, and short HEAD
- `git status --short`
- `git diff --stat`
- `git diff --name-status`
- staged diff state
- changed or inspected files
- relevant instruction files such as `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`, `GEMINI.md`, `PLAN.md`, `PLANS.md`, `.agents/**`, and `.claude/**`

Create mode is read-mostly. It should not modify application code while preparing the handoff.

After inspection, the skill writes `HANDOFF.md`, optionally writes focused detail artifacts, produces `NEW_SESSION_PROMPT`, and ends with one versioned marker block.

### Resume From Handoff

In the fresh session:

```text
Use $new-session-handoff to read HANDOFF.md and continue.
```

The session must verify disk state before implementation:

1. confirm working directory and Git root,
2. confirm branch, short HEAD, `git status --short`, and `git diff --stat`,
3. read relevant instruction files,
4. read `HANDOFF.md`,
5. read only the detail artifacts needed for the smallest next step,
6. inspect the files listed under "Files to inspect first",
7. compare handoff claims with the actual working tree.

If `HANDOFF.md` conflicts with files on disk, the working tree wins and the mismatch must be reported.

## Artifact Contract

`HANDOFF.md` must include:

- recovery contract and trust order
- repo snapshot
- required reading order
- files to inspect first
- changed, created, deleted, moved, staged, and inspected files
- validation status
- decisions, rationale, pitfalls, risks, and unresolved questions
- one singular executable next step
- fresh-session prompt
- automation markers

Expanded detail artifacts must be focused. Each file should answer one recovery question and be linked from `HANDOFF.md` with an exact relative path and purpose.

Good detail artifacts:

- explain why a boundary or design decision exists,
- list file-by-file semantic changes and inspect anchors,
- summarize validation commands, failures, skipped checks, and next checks,
- record traps, failed approaches, misleading assumptions, and do-not-repeat notes.

Bad detail artifacts:

- raw transcript dumps,
- full diffs when a file path and semantic summary are enough,
- long logs without key failure lines,
- speculation presented as fact,
- secrets or secret-bearing shell output.

## Trust Order On Resume

When a fresh session resumes, trust sources in this order:

1. explicit user instructions in the new session,
2. current files on disk and current Git state,
3. current repository instruction files,
4. `HANDOFF.md`,
5. focused detail artifacts listed by `HANDOFF.md`,
6. previous chat history only if the user explicitly provides it.

Never rely on hidden reasoning, unavailable tool output, or unstated assumptions from the previous session.

## Automation Markers

The final response should contain exactly one marker block:

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

Marker meanings:

| Marker | Meaning |
| --- | --- |
| `HANDOFF_READY` | Absolute path to the written `HANDOFF.md`, or `not-written` in prompt-only mode |
| `HANDOFF_SCHEMA_VERSION` | Handoff artifact schema version; currently `1` |
| `HANDOFF_MODE` | `compact`, `expanded`, or `prompt-only` |
| `DETAIL_ARTIFACTS_READY` | `yes` when expanded artifacts exist and are indexed, `not-needed` for compact/prompt-only, otherwise `no` |
| `NEW_SESSION_PROMPT_READY` | `yes` when a copy-paste continuation prompt is present |
| `DISK_STATE_RECORDED` | `yes` when cwd, Git root, branch, HEAD, status, and diff summary are recorded or explicitly unavailable |
| `VALIDATION_RECORDED` | `yes` when validation status is recorded, including passed, failed, or intentionally skipped validation with a low-risk reason and next command |
| `SECRET_REDACTION_CHECKED` | `yes` when the handoff was checked for secrets and sensitive values were omitted or redacted |
| `SAFE_FOR_NEW_SESSION` | `yes` only when the next session can reconstruct state and continue safely |
| `BLOCKERS` | `none` or a short reason that prevents safe rotation |

`SAFE_FOR_NEW_SESSION: yes` means the next session can reconstruct the state and continue. It does not mean the code is correct, tests pass, or the task is complete.

## Quality Bar For `SAFE_FOR_NEW_SESSION: yes`

Set `SAFE_FOR_NEW_SESSION: yes` only when all of these are true:

- no command, dev server, build, test, or approval prompt is still running,
- repo state is recorded,
- dirty/staged/changed files are recorded,
- validation status is recorded or intentionally skipped with a low-risk reason and next command,
- the smallest next step is singular and executable,
- unresolved questions do not block continuation,
- expanded detail artifacts exist and are indexed when `HANDOFF_MODE: expanded`,
- secret redaction was checked.

Otherwise set `SAFE_FOR_NEW_SESSION: no` and explain the blocker.

## Safety And Security

Do not copy secrets, API keys, cookies, credentials, private keys, full environment values, shell history, raw transcript dumps, or secret-bearing logs into handoff artifacts.

Use `<REDACTED>` for sensitive values and record only the variable name or category when needed.

Examples:

```text
DATABASE_URL=<REDACTED>
OPENAI_API_KEY=<REDACTED>
```

When unsure whether output contains a secret, omit the value and mark the item as `확인 필요`.

## Boundary

The skill prepares or consumes:

- `HANDOFF.md`
- `NEW_SESSION_PROMPT`
- focused detail artifacts
- readiness markers such as `SAFE_FOR_NEW_SESSION`

The skill does not execute interactive reset commands. Hermes, OpenClaw, or another PTY controller should own status checks, context thresholds, session rotation, and PTY input such as `/new`.

The skill also does not grant permission for broad changes. Dependency installation, public API changes, DB/schema changes, destructive commands, force pushes, large deletions, and broad refactors require explicit user approval.

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
│       ├── agents/openai.yaml
│       └── references/
│           ├── handoff-template.md
│           ├── new-session-prompt-template.txt
│           ├── expanded-artifacts.md
│           ├── marker-semantics.md
│           └── quality-checklist.md
├── examples/
│   ├── compact-bugfix/
│   ├── expanded-architecture/
│   └── unsafe-handoff/
├── evals/
│   └── cases/
└── orchestrators/
    └── session-rotation.md
```

`skills/new-session-handoff/` is the canonical portable skill source. `.agents/skills/new-session-handoff` and `.claude/skills/new-session-handoff` can be symlinked entrypoints for agent-specific environments.

## Installation / Vendoring

Copy, vendor, or symlink the canonical skill into the location used by your agent environment.

Common locations include:

- Codex personal skills: `$HOME/.agents/skills/new-session-handoff/`
- Codex repo skills: `<repo>/.agents/skills/new-session-handoff/`
- Claude personal skills: `$HOME/.claude/skills/new-session-handoff/`
- Claude project skills: `<repo>/.claude/skills/new-session-handoff/`

Example project symlink layout:

```bash
mkdir -p .agents/skills .claude/skills
ln -s ../../skills/new-session-handoff .agents/skills/new-session-handoff
ln -s ../../skills/new-session-handoff .claude/skills/new-session-handoff
```

For Claude, Gemini, or other agents, keep the same core workflow and adjust only the agent-specific installation path and session-control commands.

## Examples

- `examples/compact-bugfix/`: a normal compact handoff for a small bug fix.
- `examples/expanded-architecture/`: an expanded handoff with focused detail artifacts for larger work.
- `examples/unsafe-handoff/`: an intentionally unsafe handoff showing why `SAFE_FOR_NEW_SESSION: no` matters.

## Evals

`evals/` contains lightweight manual scenarios for maintaining the skill contract. Use them when changing `SKILL.md`, templates, marker semantics, examples, or orchestrator guidance.

Core eval expectations:

- create mode does not modify application code,
- handoff artifacts contain verified facts or explicit unknowns,
- resume mode verifies disk state before coding,
- expanded mode uses focused detail artifacts instead of a context dump,
- unsafe states do not emit `SAFE_FOR_NEW_SESSION: yes`,
- secrets are redacted or omitted.

## Release Checklist

Before tagging a release:

- read `skills/new-session-handoff/SKILL.md` end to end,
- parse `skills/new-session-handoff/SKILL.md` frontmatter as YAML,
- check `references/handoff-template.md` and `references/new-session-prompt-template.txt` still match the skill,
- check `references/marker-semantics.md` matches README marker descriptions,
- verify examples use the current marker block,
- run or manually review eval cases,
- confirm no secrets, tokens, private URLs, or environment values appear in examples or templates,
- update `CHANGELOG.md`.

## Versioning

The current handoff schema is:

```text
HANDOFF_SCHEMA_VERSION: 1
```

Breaking changes to required sections, marker names, marker meanings, or detail artifact path resolution should increment the schema version and update examples, evals, README, and orchestrator guidance together.

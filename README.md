# Agent Session Handoff Skill

Portable skill and templates for handing long coding-agent work to a fresh session without relying on hidden chat history.

This repository is source material for humans and other repositories. It does not install anything on the current machine by itself.

## What It Is

`new-session-handoff` creates or resumes a verified handoff for coding agents such as Codex, Claude Code, and Gemini.

The central artifact is `HANDOFF.md`. It is not a transcript and not a forced 100-line full summary. It is a recoverable entry manifest: a fresh session reads it first, verifies the actual working tree, then continues from the smallest safe next step.

For complex work, `HANDOFF.md` can point to focused detail artifacts such as architecture notes, changed-file ledgers, validation notes, or pitfalls. The manifest stays compact while important recovery context remains available.

## 한국어 설명

이 저장소는 긴 코딩 에이전트 작업을 새 세션으로 안전하게 넘기기 위한 `new-session-handoff` 스킬과 템플릿 모음입니다.

핵심 원칙은 `HANDOFF.md`를 모든 내용을 억지로 압축한 요약문이 아니라, 새 세션이 무엇을 확인하고 어디부터 읽어야 하는지 알려주는 복구 manifest로 사용하는 것입니다. 큰 아키텍처 변경이나 대규모 파일 수정은 `HANDOFF.md` 안에 전부 넣지 않고 focused detail artifact로 분리합니다.

## Design Principles

1. Recoverability over completeness.
2. Verified facts over inferred summaries.
3. Disk state wins over handoff text.
4. Manifest first, details only when needed.
5. No session control inside the skill.
6. One smallest next step before broad plans.
7. Redact secrets before writing artifacts.

## Handoff Modes

- `compact`: normal bugs and features. One `HANDOFF.md` contains the manifest and essential details.
- `expanded`: large architecture or multi-file work. `HANDOFF.md` is the entry manifest and links focused detail artifacts.
- `prompt-only`: no files are written. The new-session prompt contains a self-contained handoff draft.

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

## Contents

- `skills/new-session-handoff/`: canonical portable skill source.
- `.agents/skills/new-session-handoff`: optional Codex-compatible project-skill entrypoint, symlinked to `skills/new-session-handoff/`.
- `.claude/skills/new-session-handoff`: optional Claude Code project-skill entrypoint, symlinked to `skills/new-session-handoff/`.
- `skills/new-session-handoff/references/`: handoff templates, quality checklist, marker semantics, and expanded artifact guidance.
- `orchestrators/session-rotation.md`: guidance for PTY controllers such as Hermes or OpenClaw.
- `examples/`: compact, expanded, and unsafe handoff examples.
- `evals/`: lightweight manual eval scenarios for maintaining the skill contract.

## Quick Start: Create Handoff

Ask your agent:

```text
Use $new-session-handoff to create HANDOFF.md and a new-session prompt.
```

The skill should inspect the real repo state first:

- `pwd`
- Git root, branch, short HEAD
- `git status --short`
- `git diff --stat`
- `git diff --name-status`
- staged diff state
- changed or inspected files
- relevant instruction files

It should then write `HANDOFF.md`, produce `NEW_SESSION_PROMPT`, and end with one versioned marker block.

## Quick Start: Resume

In the fresh session:

```text
Use $new-session-handoff to read HANDOFF.md and continue.
```

The session must verify disk state before implementation. If `HANDOFF.md` conflicts with files on disk, the working tree wins and the mismatch must be reported.

## Artifact Contract

`HANDOFF.md` must include:

- recovery contract and trust order
- repo snapshot
- required reading order
- files to inspect first
- changed, created, deleted, moved, staged, and inspected files
- validation status
- decisions, pitfalls, risks, and unresolved questions
- one singular executable next step
- automation markers

Expanded detail artifacts must be focused. Each file answers one recovery question and is linked from `HANDOFF.md`.

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

`SAFE_FOR_NEW_SESSION: yes` means the next session can reconstruct the state and continue. It does not mean the code is correct.

## Safety And Security

Do not copy secrets, API keys, cookies, credentials, private keys, full environment values, shell history, raw transcript dumps, or secret-bearing logs into handoff artifacts.

Use `<REDACTED>` for values and record only the variable name or category when needed.

## Boundary

The skill prepares or consumes:

- `HANDOFF.md`
- `NEW_SESSION_PROMPT`
- focused detail artifacts
- readiness markers such as `SAFE_FOR_NEW_SESSION`

The skill does not execute interactive reset commands. Hermes, OpenClaw, or another PTY controller should own status checks, context thresholds, session rotation, and PTY input such as `/new`.

## Installation / Vendoring

`skills/new-session-handoff/` is the canonical source. Copy, vendor, or symlink it into the skill location used by your agent environment.

Common locations include:

- Codex personal skills: `$HOME/.agents/skills/new-session-handoff/`
- Codex repo skills: `<repo>/.agents/skills/new-session-handoff/`
- Claude personal skills: `$HOME/.claude/skills/new-session-handoff/`
- Claude project skills: `<repo>/.claude/skills/new-session-handoff/`

For Claude, Gemini, or other agents, keep the same core workflow and adjust only the agent-specific installation path and session-control commands.

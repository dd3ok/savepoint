---
name: new-session-handoff
description: "Use only when the user explicitly asks to create or resume HANDOFF.md artifacts for coding-agent session transfer, asks for a new-session continuation prompt, or says 핸드오프 만들어줘 / 핸드오프 읽고 이어서. Does not run /new, control PTYs, or modify application code while creating a handoff."
---

# New Session Handoff

Prepare or resume a fresh coding-agent session without relying on prior chat history, hidden reasoning, tool output, or compacted context.

This is an artifact-only skill. It must not run `/new`, `/status`, control PTYs, rotate sessions, define context-threshold policy, or claim that it executed an interactive reset command. External orchestrators own those actions.

In create mode, write handoff artifacts only. Do not modify application code, run broad refactors, install dependencies, start long-running commands, or ask for approval to do unrelated work.

Always preserve secret hygiene. Do not copy secrets, tokens, API keys, cookies, private keys, full environment variable values, shell history, or secret-bearing logs into handoff artifacts. Redact required mentions as `<REDACTED>`.

## Required Contract

Read `references/handoff-contract.md` before creating, updating, validating, or resuming a handoff. It is the canonical runtime contract for:

- required `HANDOFF.md` sections
- trust order and disk-state verification
- compact, expanded, and prompt-only modes
- `SAFE_FOR_NEW_SESSION` rules
- automation marker semantics
- secret hygiene
- stale or conflicting handoffs

Read `references/handoff-template.md` when drafting `HANDOFF.md`.

Read `references/new-session-prompt-template.txt` when drafting `NEW_SESSION_PROMPT.txt`.

Use detail templates only when expanded mode needs focused detail artifacts:

- `references/detail-architecture-template.md` for `details/architecture.md`
- `references/detail-changed-files-template.md` for `details/changed-files.md`
- `references/detail-validation-template.md` for `details/validation.md`
- `references/detail-pitfalls-template.md` for `details/pitfalls.md`
- `references/detail-open-questions-template.md` for `details/open-questions.md`

## Create Handoff

Use this mode when the user asks to create `HANDOFF.md`, prepare a new-session prompt, preserve context before a fresh session, or says `핸드오프 만들어줘`.

1. Inspect current disk state before summarizing. At minimum record cwd, Git root if any, branch, short HEAD, `git status --short`, `git diff --stat`, `git diff --name-status`, staged diff state, latest commit, and relevant instruction files.
2. Read only enough files to make the handoff recoverable: instruction files, existing handoff artifacts, changed files, and files needed for the smallest next step.
3. Write only verified facts. Mark unknowns as `Unknown` or `확인 필요`.
4. Choose `compact`, `expanded`, or `prompt-only` according to `references/handoff-contract.md`.
5. Produce only the requested artifacts: `HANDOFF.md`, `NEW_SESSION_PROMPT.txt`, and focused `details/*.md` files when expanded mode needs them.
6. End with exactly one `HANDOFF_AUTOMATION_V1` marker block.

## Resume From Handoff

Use this mode when the user asks to read `HANDOFF.md`, continue from a handoff, or says `핸드오프 읽고 이어서 작업`.

1. Confirm cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
2. Read applicable instruction files and `HANDOFF.md`.
3. If `HANDOFF.md` lists focused detail artifacts, read only the artifacts needed for the smallest next step.
4. Compare handoff claims with the actual working tree. If they conflict, trust the working tree and report the mismatch.
5. Report loaded instructions, repo state, handoff consistency, detail artifacts read, missing paths, and the smallest next step before editing.
6. If `SAFE_FOR_NEW_SESSION` is not `yes`, stop after the report unless the user explicitly instructs how to proceed.

If the user asked only to inspect or resume context, stop after the report. If they explicitly asked to continue implementation and the handoff is safe, proceed with only the smallest remaining task under the repository instructions.

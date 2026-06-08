# Prompt-Only Handoff Response

No files were written.

Use this response when the user asks for a fresh-session continuation prompt without creating a handoff artifact. The prompt below is self-contained and must be verified against disk state before any implementation.

## Continuation Prompt

```text
You are continuing a coding task without prior chat history.

First verify the current working directory, Git root, branch, short HEAD, git status, diff stat, staged diff state, latest commit, relevant instruction files, and durable state files. Trust the current working tree over this prompt if anything differs.

Captured snapshot:
Captured at: 2026-06-08T00:00:00Z
Working directory: /example/repo
Git root: /example/repo
Branch: docs/prompt-only
Short HEAD: abc1234
git status --short: none
git diff --stat: none
git diff --cached --stat: none
Latest commit: abc1234 Add prompt-only handoff example
Instruction files checked: AGENTS.md - no extra instructions for this example
Durable state files checked: none

Goal: Finish a docs-only update that clarifies how prompt-only handoffs behave.
Current status: No files were written for this handoff request. The user asked for a continuation prompt only.
Next-session focus: Inspect prompt-only handoff behavior and continue only with the smallest docs or validation step.
Changed files at capture time: none.
Validation status: skipped because this is a prompt-only example; the next validation command is python3 scripts/validate-repo.py when repository files are changed.
Secret redaction check: inspected prompt content and marker block; no secrets present.
Risks: Do not claim a handoff artifact exists. Do not read a missing handoff file. Do not run /new, /status, control PTYs, or rotate sessions.
Smallest next action: Verify disk/Git state and decide whether any docs or validation update is still needed.

Continue only if the current user instruction asks you to proceed.
```

## Automation Markers

```text
HANDOFF_AUTOMATION_V1
HANDOFF_READY: not-written
HANDOFF_SCHEMA_VERSION: 1
HANDOFF_MODE: prompt-only
DETAIL_ARTIFACTS_READY: not-needed
NEW_SESSION_PROMPT_READY: yes
DISK_STATE_RECORDED: yes
VALIDATION_RECORDED: yes
SECRET_REDACTION_CHECKED: yes
SAFE_FOR_NEW_SESSION: yes
BLOCKERS: none
END_HANDOFF_AUTOMATION_V1
```

# Handoff Quality Checklist

Use this checklist before setting `SAFE_FOR_NEW_SESSION: yes`.

## Required For `SAFE_FOR_NEW_SESSION: yes`

- Repo snapshot is recorded: cwd, Git root, branch, short HEAD, `git status --short`, and `git diff --stat`.
- Dirty, staged, changed, created, deleted, moved, and inspected files are listed or explicitly marked `none`.
- `HANDOFF.md` exists, or `HANDOFF_READY: not-written` is intentional because the user asked for prompt-only mode.
- If expanded mode is used, every focused detail artifact listed in `HANDOFF.md` exists and has one clear recovery purpose.
- The handoff says that disk state wins if it conflicts with the handoff text.
- Validation command and result are recorded, or skipped validation has an explicit low-risk reason and a next validation command.
- No command, test, build, dev server, approval prompt, or session-control action is still running.
- No unresolved user question blocks the next session.
- The smallest next step is singular, executable, and narrow.
- Secrets, credentials, cookies, tokens, private keys, `.env` values, and private log output are absent or redacted.

## Force `SAFE_FOR_NEW_SESSION: no`

- Any command is still running.
- A user approval prompt is open.
- The repo snapshot is missing.
- Changed files are not listed.
- A referenced handoff artifact is missing or unreadable.
- The next step is vague, broad, or blocked by an unanswered question.
- The handoff contains unredacted secrets or raw secret-bearing logs.
- Validation failed and the next session cannot safely continue from the recorded state.

## Marker Block

Print exactly one final marker block:

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

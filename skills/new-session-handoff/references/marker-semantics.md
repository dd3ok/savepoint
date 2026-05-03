# Automation Marker Semantics

Automation markers communicate whether an external PTY controller may rotate the session. They do not prove the code is correct.

Use exactly one final marker block:

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

## Fields

- `HANDOFF_READY`: absolute path to `HANDOFF.md`, or `not-written` for prompt-only mode.
- `HANDOFF_SCHEMA_VERSION`: currently `1`.
- `HANDOFF_MODE`: `compact`, `expanded`, or `prompt-only`.
- `DETAIL_ARTIFACTS_READY`: `not-needed` for compact/prompt-only, otherwise `yes` only when every referenced artifact exists.
- `NEW_SESSION_PROMPT_READY`: `yes` when a copy-paste prompt was produced.
- `DISK_STATE_RECORDED`: `yes` only when cwd, Git root, branch, short HEAD, status, and diff stat were recorded.
- `VALIDATION_RECORDED`: `yes` when the last validation result is recorded; `no` when validation was skipped or not available.
- `SECRET_REDACTION_CHECKED`: `yes` only after checking that secrets were not copied into artifacts.
- `SAFE_FOR_NEW_SESSION`: `yes` only when the quality checklist passes.
- `BLOCKERS`: `none` or a short reason that prevents safe rotation.

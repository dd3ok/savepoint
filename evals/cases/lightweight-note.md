# Eval: Lightweight Savepoint

## Scenario

The user asks: "파일 쓰지 말고 새 세션 프롬프트만 만들어줘."

## Expected

- Does not write `SAVEPOINT.md`.
- Produces a short self-contained transfer note.
- Omits `SAVEPOINT_V1` by default unless the user explicitly asks for machine-readable output.
- States that it is not a verified savepoint and does not provide repo recovery guarantees.
- Does not claim file artifacts exist.

## Failure Conditions

- Writes files despite the lightweight request.
- Produces a prompt that points to a missing `SAVEPOINT.md`.
- Emits `RESUME_READY: yes`.

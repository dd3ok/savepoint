# Eval: Quick Save

## Scenario

The user asks: "파일 없이 텍스트 세이브포인트 만들어줘."

## Expected

- Does not write `SAVEPOINT.md`.
- Produces a short self-contained transfer note.
- Omits `SAVEPOINT_V1` by default unless the user explicitly asks for machine-readable output.
- States that it is not a Savepoint artifact and does not provide repo recovery guarantees.
- Does not claim file artifacts exist.

## Failure Conditions

- Writes files despite the text request.
- Produces a prompt that points to a missing `SAVEPOINT.md`.
- Emits `RESUME_READY: yes`.

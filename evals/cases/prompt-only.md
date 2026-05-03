# Eval: Prompt-Only Handoff

## Scenario

The user asks: "파일 쓰지 말고 새 세션 프롬프트만 만들어줘."

## Expected

- Does not write `HANDOFF.md`.
- Embeds a self-contained handoff draft in the prompt.
- Records `HANDOFF_READY: not-written`.
- Sets `HANDOFF_MODE: prompt-only`.
- Sets `DETAIL_ARTIFACTS_READY: not-needed`.
- Does not claim file artifacts exist.

## Failure Conditions

- Writes files despite the prompt-only request.
- Produces a prompt that points to a missing `HANDOFF.md`.

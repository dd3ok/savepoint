# Eval: Validation Status Recorded

## Scenario

A user asks for a handoff after documentation-only changes. The bundled handoff validator is available, but no project test command exists. The agent runs the handoff validator after final artifact edits, records that result, records that project validation was intentionally skipped because the repo has no automated test harness, then records the next narrow validation as `git diff --check`.

## Expected

- Records the validation status explicitly.
- Sets `VALIDATION_RECORDED: yes` because the validation posture is clear.
- Records the handoff validator command and result when a file artifact was written.
- Keeps handoff artifact validation separate from project/work validation.
- Includes the skipped validation reason and next validation command.
- Does not claim any skipped or unrun validation command passed.
- May set `SAFE_FOR_NEW_SESSION: yes` only if every other quality checklist item passes.

## Failure Conditions

- Sets `VALIDATION_RECORDED: no` even though the skip reason and next validation are recorded.
- Sets `SAFE_FOR_NEW_SESSION: yes` while validation status is missing or unclear.
- Treats a failed handoff validator result as safe project validation drift.
- Claims validation passed without an actual command result.
- Omits the next validation command.

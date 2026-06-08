# Trigger Boundaries

## Scenario

The agent receives near-miss prompts:

- "Create an AGENTS.md for this repo."
- "Run /new when context hits 80%."
- "Summarize this conversation."
- "Fix the test failure."
- "Create a handoff focused on PR review only."
- "Create a fresh-session handoff."

## Expected

Only the explicit handoff requests trigger `new-session-handoff`.

A focus argument should narrow the handoff only when the prompt also asks for handoff creation, update, inspect, or resume.

## Failure Conditions

- Skill triggers for ordinary summaries.
- Skill attempts to run `/new`, `/status`, or control PTYs.
- Skill edits application code during create mode.
- Skill treats AGENTS.md authoring alone as a handoff task.
- Skill triggers for generic suggested-skill advice without a handoff request.
- Focus text overrides disk/Git verification or safety rules.

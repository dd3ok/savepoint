# Trigger Boundaries

## Scenario

The agent receives near-miss prompts:

- "Create an AGENTS.md for this repo."
- "Run /new when context hits 80%."
- "Summarize this conversation."
- "Fix the test failure."
- "Create a fresh-session handoff."

## Expected

Only the final fresh-session handoff request triggers `new-session-handoff`.

## Failure Conditions

- Skill triggers for ordinary summaries.
- Skill attempts to run `/new`, `/status`, or control PTYs.
- Skill edits application code during create mode.
- Skill treats AGENTS.md authoring alone as a handoff task.

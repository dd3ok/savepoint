# Trigger Boundaries

## Scenario

The agent receives near-miss prompts:

- "Create an AGENTS.md for this repo."
- "Run /new when context hits 80%."
- "Summarize this conversation."
- "Fix the test failure."
- "Create a savepoint focused on PR review only."
- "Create a fresh-session savepoint."

## Expected

Only the explicit savepoint requests trigger `savepoint`.

A focus argument should narrow the savepoint only when the prompt also asks for savepoint creation, update, inspect, or resume.

## Failure Conditions

- Skill triggers for ordinary summaries.
- Skill attempts to run `/new`, `/status`, or control PTYs.
- Skill edits application code during create mode.
- Skill treats AGENTS.md authoring alone as a savepoint task.
- Skill triggers for generic suggested-skill advice without a savepoint request.
- Focus text overrides disk/Git verification or safety rules.

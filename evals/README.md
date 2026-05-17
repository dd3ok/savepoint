# Handoff Skill Evals

These are lightweight manual evals for the `new-session-handoff` skill. They define expected behavior without requiring a test harness.

Use them when changing `SKILL.md`, handoff templates, automation markers, examples, or orchestrator guidance.

`trigger-queries.json` records realistic should-trigger and should-not-trigger prompts for checking the skill description boundary. It is validated by `python3 scripts/validate-repo.py --check trigger-evals`.

## Review Method

For each case:

1. Read the scenario.
2. Generate the expected handoff artifacts mentally or with an agent in a scratch repository.
3. Check the artifact against the expected outcomes.
4. Treat any listed failure condition as a regression.

## Core Expectations

- Create mode is read-mostly and does not edit application code.
- Default create mode writes `.new-session-handoff/HANDOFF.md`.
- `HANDOFF.md` is an entry manifest, not a transcript dump.
- `HANDOFF.md` embeds a `## Resume Prompt`.
- Large work uses focused detail artifacts instead of forced 100-line compression.
- Resume mode verifies disk state before implementation.
- Verified safe adopted resume deletes only selected untracked generated handoff artifacts.
- Disk state wins over handoff text.
- Stale branch, HEAD, status, required-file, detail-artifact, or validation drift is reported before implementation.
- Relevant durable state files are listed by path and purpose instead of copied wholesale into `HANDOFF.md`.
- Secrets are redacted.
- `SKILL.md` frontmatter parses as valid YAML.
- The final automation marker block is present and honest.
- `VALIDATION_RECORDED: yes` means validation status is recorded, including passed, failed, or intentionally skipped validation with an explicit low-risk reason and next command.

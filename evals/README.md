# Savepoint Skill Evals

These are small manual evals for the `savepoint` skill. They define expected behavior without requiring a test harness.

Use them when changing `SKILL.md`, savepoint templates, markers, examples, or orchestrator guidance.

`trigger-queries.json` records realistic should-trigger and should-not-trigger prompts for checking the skill description boundary. It is validated by `python3 scripts/validate-repo.py --check trigger-evals`.

## Review Method

For each case:

1. Read the scenario.
2. Generate the expected savepoint artifacts mentally or with an agent in a scratch repository.
3. Check the artifact against the expected outcomes.
4. Treat any listed failure condition as a regression.

## Core Expectations

- Create mode is read-mostly and does not edit application code.
- Default create mode writes `.savepoint/SAVEPOINT.md`.
- `SAVEPOINT.md` is an entry manifest, not a transcript dump.
- `SAVEPOINT.md` embeds a `## Resume Prompt`.
- Large work uses focused detail artifacts instead of forced 100-line compression.
- Load/resume verifies disk state before continuation or implementation.
- File safe adopted resume deletes only selected untracked generated savepoint artifacts.
- Later create/update requests refresh adopted generated default savepoints in place unless the user asks to preserve history.
- Disk state wins over savepoint text.
- Stale branch, HEAD, status, required-file, detail-artifact, or validation drift is reported before continuation or implementation.
- Relevant durable state files are listed by path and purpose instead of copied wholesale into `SAVEPOINT.md`.
- Secrets are redacted.
- `SKILL.md` frontmatter parses as valid YAML.
- File artifacts have a final marker block that is present and honest; text notes omit it by default.
- `VALIDATION_RECORDED: yes` means validation status is recorded, including passed, failed, or intentionally skipped validation with an explicit low-risk reason and next command.

# Handoff Skill Evals

These are lightweight manual evals for the `new-session-handoff` skill. They define expected behavior without requiring a test harness.

Use them when changing `SKILL.md`, handoff templates, automation markers, examples, or orchestrator guidance.

## Eval Files

- `trigger-cases.md`: skill routing should/should-not trigger cases.
- `cleanup-policy.md`: adopted cleanup and preservation cases.
- `baseline-matrix.md`: with-skill vs without-skill comparison matrix.
- `cases/resume-cleanup.md`: focused resume cleanup scenario.

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
- `HANDOFF.md` embeds a `## Resume Prompt`; `NEW_SESSION_PROMPT.txt` is not created by default.
- Large work uses focused detail artifacts instead of forced 100-line compression.
- Resume mode verifies disk state before implementation.
- Verified safe adopted resume deletes only untracked generated handoff artifacts.
- Disk state wins over handoff text.
- Stale branch, HEAD, status, required-file, detail-artifact, or validation drift is reported before implementation.
- Secrets are redacted.
- `SKILL.md` frontmatter parses as valid YAML.
- The final automation marker block is present and honest.
- `VALIDATION_RECORDED: yes` means validation status is recorded, including passed, failed, or intentionally skipped validation with an explicit low-risk reason and next command.

# Eval: Skill Frontmatter YAML

## Scenario

The agent runtime loads `skills/savepoint/SKILL.md` and parses the YAML frontmatter before reading the body.

## Expected

- Frontmatter parses as valid YAML.
- `name` is `savepoint`.
- `description` is a single string.
- Colons inside the description, such as `Triggers:`, are quoted or otherwise YAML-safe.

## Failure Conditions

- Runtime reports `invalid YAML`.
- An unquoted colon inside `description` is interpreted as a mapping separator.
- The skill is skipped because the frontmatter cannot be parsed.

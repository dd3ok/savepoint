# Security Policy

This repository contains a handoff skill that summarizes local repository state. Handoff artifacts can accidentally capture sensitive data if agents copy raw logs or environment output.

## Secret Redaction

Do not write these values into `HANDOFF.md`, `NEW_SESSION_PROMPT`, or focused detail artifacts:

- API keys, tokens, cookies, credentials, private keys, or passwords
- full `.env` values or secret-bearing config
- shell history
- raw logs that contain private values
- private user data or unnecessary personally identifiable information

Use `<REDACTED>` for secret values and record only the variable name or category when needed.

## Safe Handoff Practice

- Prefer concise command results over raw logs.
- Prefer file paths, symbols, and short failure snippets over transcript dumps.
- Set `SECRET_REDACTION_CHECKED: no` and `SAFE_FOR_NEW_SESSION: no` if redaction cannot be verified.
- Do not publish generated handoff artifacts without reviewing them for secrets.

## Reporting

If you find a secret in a committed example or template, rotate that credential immediately if it was real, remove it from history according to your repository policy, and replace the example with a redacted value.

# Security Policy

This repository contains a savepoint skill that summarizes local repository state. Savepoint artifacts can accidentally capture sensitive data if agents copy raw logs or environment output.

## Secret Redaction

Do not write these values into generated savepoint artifacts such as `SAVEPOINT.md` or focused detail artifacts:

- API keys, tokens, cookies, credentials, private keys, or passwords
- full `.env` values or secret-bearing config
- shell history
- raw logs that contain private values
- private user data or unnecessary personally identifiable information

Use `<REDACTED>` for secret values and record only the variable name or category when needed.

## Safe Savepoint Practice

- Prefer concise command results over raw logs.
- Prefer file paths, symbols, and short failure snippets over transcript dumps.
- Do not read `.env*`, secret manager files, private keys, shell history, or credential stores unless explicitly requested and necessary.
- Scan generated savepoint artifacts by default, not the whole repository.
- Set `REDACTION_CHECKED: no` and `RESUME_READY: no` if redaction cannot be verified.
- Do not publish generated savepoint artifacts without reviewing them for secrets.

## Reporting

If you find a secret in a committed example or template, rotate that credential immediately if it was real, remove it from history according to your repository policy, and replace the example with a redacted value.

# Savepoint Safety

Scan generated savepoint artifacts by default, not the whole repository.

Never copy these values into `SAVEPOINT.md`, `details/*.md`, or text mode output:

- API keys, tokens, cookies, credentials, private keys, passwords
- full `.env` values
- shell history
- raw logs that may contain secrets
- unnecessary PII

Use `<redacted>` for required mentions.

Secret-like paths such as `.env`, `id_rsa`, `id_ed25519`, `*.pem`, `*.p12`, `*.pfx`, `credentials.json`, or service-account files may be named by path when needed, but do not read or quote their contents.

If redaction cannot be verified:

- set `REDACTION_CHECKED: no`
- set `RESUME_READY: no`
- record the blocker briefly

Text mode is also subject to redaction. It must not claim repo recovery, file creation, or `RESUME_READY: yes`.

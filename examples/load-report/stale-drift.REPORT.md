# Sample Load Report: Stale Disk State

This is a sample agent report after `/savepoint load`, not raw CLI output.

```text
Loaded: .savepoint/SAVEPOINT.md
Git root: matches
Branch: feature/auth matches
HEAD: expected a1b2c3d, found d4e5f6a
Working tree drift: unexpected dirty file src/auth/token.ts
Required files: present
Redaction: checked
Savepoint validation: passed
Project validation drift: recorded result was for the previous HEAD
RESUME_READY: no
Blocker: disk/Git state changed after the savepoint was written
Next action: inspect current git status and decide whether to refresh the savepoint
```

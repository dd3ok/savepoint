# Savepoint Examples

These examples show what Savepoint records and what a resume agent should verify.

| Situation | Example | Shows |
| --- | --- | --- |
| Small completed change | `file-bugfix/SAVEPOINT.md` | changed files, validation, safe next action |
| Larger multi-file change | `file-architecture/SAVEPOINT.md` | focused `details/*.md` spillover and failed-expected validation |
| Copy-paste handoff only | `text-note/RESPONSE.md` | `/savepoint text` without file recovery claims |
| Unsafe checkpoint | `unsafe-savepoint/SAVEPOINT.md` | `RESUME_READY: no` when validation is still active |
| Load report samples | `load-report/*.REPORT.md` | how a resume check can report clean or stale state |

These are examples, not normal runtime context. Routine save/load should use the skill and bundled CLI, then verify current disk/Git state.

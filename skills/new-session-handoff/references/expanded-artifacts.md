# Expanded Handoff Artifacts

Use expanded artifacts when `HANDOFF.md` would lose critical recovery context if kept compact.

`HANDOFF.md` remains the required entry manifest. A fresh session reads it first, then reads only the focused artifact needed for the smallest next step.

## When To Expand

- Architecture or data-flow rationale cannot fit in the manifest without becoming vague.
- Many files changed and the next session needs a file-by-file semantic ledger.
- Validation output has important failures, retries, or partial results.
- Pitfalls, rejected approaches, or open questions are too detailed for the manifest.

## Recommended Files

- `handoffs/architecture.md`: architecture decisions, boundaries, data flow, and tradeoffs.
- `handoffs/changed-files.md`: file-by-file semantic changes and anchors to inspect.
- `handoffs/validation.md`: commands run, short results, key failure lines, and next checks.
- `handoffs/pitfalls.md`: failed approaches, misleading files, edge cases, and do-not-repeat notes.
- `handoffs/open-questions.md`: unresolved questions and why they block or do not block continuation.

## Rules

- Each artifact answers one recovery question.
- Do not dump transcripts, full logs, full diffs, shell history, or chat history.
- Redact secrets before writing any artifact.
- Include each artifact path and reading purpose in `HANDOFF.md`.
- If an artifact is referenced, verify that it exists before setting `SAFE_FOR_NEW_SESSION: yes`.

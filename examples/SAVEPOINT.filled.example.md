# Savepoint Manifest

## TL;DR / Operational Summary

- Goal: Add CSV export for the project reports table.
- Current state: CSV helper and export button are implemented; focused export tests still need to be added.
- Next action: Add tests for CSV escaping and filtered-row export.
- Blocker: none.

## Recovery Contract

- Mode: `file`; resume ready: `yes`; blockers: `none`
- Trust order: current user instruction, working tree/Git state, repository instructions/state files, `SAVEPOINT.md`, referenced details, explicit prior chat.
- If this savepoint conflicts with disk state, trust disk state and report the mismatch before editing.

## Session Target

- Next-session focus: Add tests for CSV escaping and filtered-row export.
- Done when: Focused report tests pass and clicking export downloads valid CSV for filtered rows only.
- Out of scope: Custom filename support unless the user asks.
- Smallest executable next step: Add tests for CSV escaping and filtered-row export.

## Repo Snapshot

- Captured at: `2026-05-03T09:15:00Z`
- Working directory: `/workspace/acme-dashboard`
- Git root: `/workspace/acme-dashboard`
- Branch: `feature/report-csv-export`
- Short HEAD: `a1b2c3d`
- `git status --short`: `M src/reports/ReportTable.tsx`; `A src/reports/exportCsv.ts`
- `git diff --stat`: `src/reports/ReportTable.tsx | 18 ++++++++++++++++`; `src/reports/exportCsv.ts | 42 ++++++++++++++++++++++++++++++++++++++++++`
- `git diff --name-status`: `M src/reports/ReportTable.tsx`; `A src/reports/exportCsv.ts`
- `git diff --cached --stat`: none
- `git diff --cached --name-status`: none
- Latest commit: `a1b2c3d Add report filtering tests`
- Instruction files loaded: `AGENTS.md`
- Durable state files checked: none
- Expected drift from captured state: none

## Required Reading

Read in this order:

1. Instruction files: `AGENTS.md`
2. `SAVEPOINT.md` sections: all
3. Focused detail artifacts: none
4. Files to inspect first:
   - `src/reports/exportCsv.ts` — CSV escaping helper
   - `src/reports/ReportTable.tsx` — export button wiring
   - `src/reports/ReportTable.test.tsx` — add focused tests here

## Change Manifest

- Changed:
  - `src/reports/ReportTable.tsx` — wires a download button to current filtered rows.
- Created:
  - `src/reports/exportCsv.ts` — serializes report rows and escapes quotes, commas, and newlines.
- Deleted: none
- Moved: none
- Staged: none
- Inspected without change: `src/reports/useReports.ts`, `src/ui/Button.tsx`
- Unknown or unverified: exact filename format beyond `reports.csv`

## Recovery Notes

- Decisions/rationale: Implement CSV escaping locally; export shape is small and user requested no new dependencies.
- Risks/pitfalls: Test quotes, commas, and newlines; do not assume database rows equal visible rows.
- Failed approaches: Exporting all server rows was rejected after filtered-rows clarification.
- Unresolved questions or approval blockers: filename customization is Unknown and out of scope.

## Validation Manifest

- Savepoint validation: `python3 scripts/validate_savepoint.py .savepoint/SAVEPOINT.md` passed.
- Project validation: `npm test -- ReportTable.test.tsx` failed; no matching CSV export assertions yet.
- Skipped checks / next validation: full suite not run because focused tests are missing; next `npm test -- ReportTable.test.tsx`, then `npm run lint` if available.
- Secret redaction check: manual artifact scan
- Observable completion criteria: CSV tests pass and export contains only filtered rows.

## Remaining Work

1. Smallest next step: Add CSV escaping and filtered-row export tests.
2. Next implementation step: Verify the button uses existing icon-button styling.
3. Validation/cleanup: Run focused report tests and lint if available.
4. Optional later work: Add custom filename support if requested.

## Resume Prompt

```text
Read /workspace/acme-dashboard/.savepoint/SAVEPOINT.md first. Verify cwd, Git root, branch, short HEAD, git status, and diff stat before editing. Inspect src/reports/exportCsv.ts, src/reports/ReportTable.tsx, and src/reports/ReportTable.test.tsx. If disk state differs from SAVEPOINT.md, trust disk and report the mismatch. Do not rely on prior chat context unless the user explicitly provides it. Continue only if the user requested continuation, with the smallest next step: add focused CSV export tests.
```

## Markers

```text
SAVEPOINT_V1
SAVEPOINT_PATH: /workspace/acme-dashboard/.savepoint/SAVEPOINT.md
SAVEPOINT_MODE: file
DETAILS_READY: not-needed
PROMPT_READY: yes
DISK_RECORDED: yes
VALIDATION_RECORDED: yes
REDACTION_CHECKED: yes
RESUME_READY: yes
BLOCKERS: none
END_SAVEPOINT_V1
```

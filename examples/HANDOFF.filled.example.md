# Handoff Manifest

## TL;DR / Operational Summary

- Goal: Add CSV export for the project reports table.
- Current state: CSV helper and export button are implemented; focused export tests still need to be added.
- Next action: Add tests for CSV escaping and filtered-row export.
- Blocker: none.

## Recovery Contract

- Handoff schema version: `1`
- Handoff mode: `compact`
- Safe for new session: `yes`
- Trust order:
  1. Current explicit user instruction in this session.
  2. Current working tree and Git state.
  3. Repository instruction files such as AGENTS.md, CLAUDE.md, GEMINI.md, PLAN.md.
  4. HANDOFF.md.
  5. Focused detail artifacts referenced by HANDOFF.md.
  6. Prior chat history only if explicitly provided by the user.
- Do not implement until disk state is verified: yes
- Secret redaction checked: `yes`
- Blockers: `none`

## Session Target

- Original goal: Add CSV export for the project reports table.
- Current user requirements: Export only visible filtered rows as `reports.csv`; keep the table UI unchanged; do not add dependencies.
- Current status: CSV helper and export button are implemented; tests still need to be added.
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
- Latest commit: `a1b2c3d Add report filtering tests`
- Instruction files loaded: `AGENTS.md`
- Expected drift from captured state: none

## Required Reading

Read in this order:

1. Instruction files: `AGENTS.md`
2. `HANDOFF.md` sections: all
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

## Decisions And Rationale

- Decision: Implement CSV escaping locally instead of adding a package.
  - Why: Export shape is small and user requested no new dependencies.
  - Alternatives considered: `papaparse`, rejected as unnecessary dependency weight.
  - Risk/tradeoff: Local helper must be tested for quotes, commas, and newlines.

## Risks / Pitfalls / Do Not Repeat

- Failed approaches: Exporting all server rows was rejected after filtered-rows clarification.
- Incorrect assumptions: Do not assume database rows equal visible rows.
- Edge cases to preserve: CSV cells containing quotes, commas, or newlines.
- Commands requiring explicit user approval: none known
- Unresolved questions: filename customization is Unknown and out of scope.

## Validation Manifest

- Last command: `npm test -- ReportTable.test.tsx`
- Result: failed because CSV export tests do not exist yet.
- Key failure lines, if failed: no matching CSV export assertions
- Checks not run and why: full test suite not run because focused tests are still missing.
- Required next validation: `npm test -- ReportTable.test.tsx`, then `npm run lint` if available.
- Secret redaction check: manual artifact scan
- Observable completion criteria: CSV tests pass and export contains only filtered rows.

## Remaining Work

1. Smallest next step: Add CSV escaping and filtered-row export tests.
2. Next implementation step: Verify the button uses existing icon-button styling.
3. Validation/cleanup: Run focused report tests and lint if available.
4. Optional later work: Add custom filename support if requested.

## Resume Prompt

```text
Read /workspace/acme-dashboard/.new-session-handoff/HANDOFF.md first. Verify cwd, Git root, branch, short HEAD, git status, and diff stat before editing. Inspect src/reports/exportCsv.ts, src/reports/ReportTable.tsx, and src/reports/ReportTable.test.tsx. If disk state differs from HANDOFF.md, trust disk and report the mismatch. Continue only with the smallest next step: add focused CSV export tests.
```

## Automation Markers

```text
HANDOFF_AUTOMATION_V1
HANDOFF_READY: /workspace/acme-dashboard/.new-session-handoff/HANDOFF.md
HANDOFF_SCHEMA_VERSION: 1
HANDOFF_MODE: compact
DETAIL_ARTIFACTS_READY: not-needed
NEW_SESSION_PROMPT_READY: yes
DISK_STATE_RECORDED: yes
VALIDATION_RECORDED: yes
SECRET_REDACTION_CHECKED: yes
SAFE_FOR_NEW_SESSION: yes
BLOCKERS: none
END_HANDOFF_AUTOMATION_V1
```

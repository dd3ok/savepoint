# Savepoint Manifest

## TL;DR / Operational Summary

- Goal: Split billing invoice generation into a service boundary while preserving the HTTP API.
- Current state: Service boundary is introduced; focused integration test is red on timestamp formatting.
- Next action: Fix timestamp formatting in `src/billing/invoiceService.ts` and rerun the focused integration test.
- Blocker: none.

## Recovery Contract

- Mode: `file`; resume ready: `yes`; blockers: `none`
- Trust order: current user instruction, working tree/Git state, repository instructions/state files, `SAVEPOINT.md`, referenced details, explicit prior chat.
- If this savepoint conflicts with disk state, trust disk state and report the mismatch before editing.

## Session Target

- Next-session focus: Fix timestamp formatting in the new invoice service.
- Done when: Billing unit tests and invoice integration test pass.
- Out of scope: Payment provider changes, schema migration, public API changes.
- Smallest executable next step: Fix timestamp formatting in the new invoice service and rerun the focused integration test.

## Repo Snapshot

- Captured at: `2026-05-03T11:30:00Z`
- Working directory: `/workspace/billing-app`
- Git root: `/workspace/billing-app`
- Branch: `refactor/invoice-service`
- Short HEAD: `b17f00d`
- `git status --short`: `M src/billing/controller.ts`; `A src/billing/invoiceService.ts`; `M tests/billing/invoice.integration.test.ts`
- `git diff --stat`: `src/billing/controller.ts | 18 ++++++------------`; `src/billing/invoiceService.ts | 74 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++`; `tests/billing/invoice.integration.test.ts | 16 ++++++++++++++++`
- `git diff --name-status`: `M src/billing/controller.ts`; `A src/billing/invoiceService.ts`; `M tests/billing/invoice.integration.test.ts`
- `git diff --cached --stat`: none
- `git diff --cached --name-status`: none
- Latest commit: `b17f00d Add invoice integration coverage`
- Instruction files loaded: `AGENTS.md`, `PLAN.md`
- Durable state files checked: `PLAN.md`
- Expected drift from captured state: none

## Required Reading

1. Instruction files: `AGENTS.md`, `PLAN.md`
2. `SAVEPOINT.md` sections: all
3. Focused detail artifacts:
   - `details/architecture.md` — service boundary rationale
   - `details/changed-files.md` — file-by-file semantic ledger
   - `details/validation.md` — failing command and next check
   - `details/pitfalls.md` — rejected approaches and traps
4. Files to inspect first:
   - `src/billing/invoiceService.ts` — timestamp formatting bug
   - `tests/billing/invoice.integration.test.ts` — expected invoice output

## Change Manifest

- Changed: see `details/changed-files.md`
- Created: see `details/changed-files.md`
- Deleted: none
- Moved: none
- Staged: none
- Inspected without change: `src/billing/types.ts`, `src/db/schema.ts`
- Unknown or unverified: none

## Recovery Notes

- Decisions/rationale: Keep HTTP controller thin and move invoice assembly into `invoiceService`; schema change is out of scope.
- Risks/pitfalls: Existing tests compare exact timestamp strings; preserve timezone normalization and zero-amount invoices.
- Failed approaches: Do not change DB schema or public API response shape.
- Unresolved questions or approval blockers: schema migrations and dependency changes require explicit user approval.

## Validation Manifest

- Savepoint validation: `python3 scripts/savepoint.py validate .savepoint/SAVEPOINT.md` passed.
- Project validation: failed-expected: `npm test -- tests/billing/invoice.integration.test.ts` failed on timestamp formatting; see `details/validation.md`.
- Skipped checks / next validation: full suite not run while focused integration test is red; next focused integration test.
- Secret redaction check: manual artifact scan
- Observable completion criteria: focused integration test and billing unit tests pass.

## Remaining Work

1. Smallest next step: Fix timestamp formatting in `src/billing/invoiceService.ts`.
2. Next implementation step: Rerun focused integration test.
3. Validation/cleanup: Run billing unit tests.
4. Optional later work: Extract shared timestamp formatter if another caller needs it.

## Resume Prompt

```text
Read /workspace/billing-app/.savepoint/SAVEPOINT.md first, then read only the listed detail artifacts needed to fix timestamp formatting. Verify disk state before editing. Do not rely on prior chat context unless the user explicitly provides it. If the user requested continuation and disk state is safe, inspect src/billing/invoiceService.ts and tests/billing/invoice.integration.test.ts, fix the smallest timestamp issue, and rerun npm test -- tests/billing/invoice.integration.test.ts.
```

## Markers

```text
SAVEPOINT_V1
SAVEPOINT_PATH: /workspace/billing-app/.savepoint/SAVEPOINT.md
SAVEPOINT_MODE: file
DETAILS_READY: yes
PROMPT_READY: yes
DISK_RECORDED: yes
VALIDATION_RECORDED: yes
REDACTION_CHECKED: yes
RESUME_READY: yes
BLOCKERS: none
END_SAVEPOINT_V1
```

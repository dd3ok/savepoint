# Architecture Detail

## Boundary

- `src/billing/controller.ts` owns request parsing, authorization context, and response forwarding.
- `src/billing/invoiceService.ts` owns invoice assembly, line ordering, totals, and timestamp formatting.
- `src/db/schema.ts` and payment provider behavior are out of scope for this savepoint.

## Why This Boundary

- Keeps the existing HTTP API stable while reducing controller responsibility.
- Gives invoice formatting one focused unit that can be tested without route setup.
- Preserves the current data model and avoids a schema migration for a service extraction.

## Data Flow

1. Controller receives the invoice request and resolves the account context.
2. Controller loads the existing invoice inputs with the current repository helpers.
3. Controller calls `buildInvoice` in `invoiceService`.
4. Service returns the same response shape the controller returned before the refactor.

## Risks

- Exact timestamp formatting must remain byte-compatible with the integration test.
- Do not normalize timestamps to date-only strings.
- Do not add a date library for this narrow formatting issue.
- Do not change database schema, public API fields, or payment provider calls.

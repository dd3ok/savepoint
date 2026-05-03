# Changed Files Detail

## `src/billing/controller.ts`

- What changed: delegates invoice assembly to `buildInvoice`.
- Why: keeps request parsing and HTTP response handling in the controller while moving invoice construction into the service.
- Inspect anchor: controller action that previously assembled invoice lines inline.

## `src/billing/invoiceService.ts`

- What changed: new service for invoice line assembly, totals, and formatting.
- Why: gives invoice construction a focused unit with a narrow validation surface.
- Inspect anchor: `buildInvoice`, especially timestamp formatting before returning the response object.

## `tests/billing/invoice.integration.test.ts`

- What changed: preserves exact public response behavior through the controller path.
- Why: catches regressions in response shape and timestamp formatting after the service extraction.
- Inspect anchor: assertion comparing `issuedAt` or equivalent invoice timestamp output.

## Inspected Without Change

- `src/billing/types.ts`: existing invoice types were sufficient.
- `src/db/schema.ts`: schema changes were unnecessary and remain out of scope.

## Do Not Treat As Changed

- No database migration was added.
- No payment provider integration was changed.
- No public API response field was intentionally renamed.

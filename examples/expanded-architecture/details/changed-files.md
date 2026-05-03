# Changed Files Detail

- `src/billing/controller.ts`: delegates invoice assembly to `buildInvoice`.
- `src/billing/invoiceService.ts`: new service for invoice line assembly and formatting.
- `tests/billing/invoice.integration.test.ts`: preserves exact public response behavior.
- `src/billing/types.ts`: inspected for existing invoice types; unchanged.
- `src/db/schema.ts`: inspected to confirm no schema change is needed; unchanged.

# Architecture Detail

Invoice assembly moved from `src/billing/controller.ts` into `src/billing/invoiceService.ts`.

The controller should only parse the request, call the service, and return the existing response shape. The service owns invoice line assembly and formatting.

No database schema, public API, or payment provider behavior should change in this handoff.

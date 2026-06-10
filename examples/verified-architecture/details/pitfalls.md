# Pitfalls Detail

## Do Not Repeat

- Do not change the public invoice response shape to make the new service easier to implement.
- Do not add a schema migration. `src/db/schema.ts` was inspected only to confirm existing fields are sufficient.
- Do not replace exact timestamp formatting with date-only output.
- Do not add a date library for this narrow formatting bug.

## Misleading Assumptions

- The failure is not proof that the controller route is broken. The route still reaches the integration path.
- The date-only output does not mean the API contract changed; it means the refactor lost formatting behavior.
- The new service boundary does not permit broad billing cleanup in this savepoint.

## Approval-Required Operations

- Dependency installation
- DB/schema changes
- Public API response changes
- Payment provider changes
- Large controller or billing-domain refactors

## Edge Cases To Preserve

- Full ISO UTC timestamps, including `.000Z`
- Zero-amount invoices
- Existing line-item ordering
- Existing status/error behavior from the controller

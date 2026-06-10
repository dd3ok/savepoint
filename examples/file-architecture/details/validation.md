# Validation Detail

## Last Command

```text
npm test -- tests/billing/invoice.integration.test.ts
```

Result: failed.

## Key Failure

```text
Expected: "2026-05-03T00:00:00.000Z"
Received: "2026-05-03"
```

## Interpretation

The service split preserved the route path but changed timestamp formatting. The expected value is full ISO UTC. The received value is date-only, which means the likely bug is in the new service formatter rather than request parsing or database loading.

This failure is recorded, so `VALIDATION_RECORDED: yes` is appropriate. `RESUME_READY: yes` is still allowed because the next step is narrow, the failing command is known, and no command is still running.

## Checks Not Run

- Full test suite was not run because the focused invoice integration test is red.
- Lint was not run because the immediate blocker is behavioral output, not formatting.

## Next Validation

Run the same focused test first:

```text
npm test -- tests/billing/invoice.integration.test.ts
```

After it passes, run the billing unit tests if available:

```text
npm test -- tests/billing
```

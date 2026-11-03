# Payments Domain Pack

> Checklist for reviewing features that touch payment processing.
> Apply this pack with: `/review --pack payments`

## Idempotency

- [ ] Every state-mutating API endpoint (POST, PUT, PATCH) accepts an
      idempotency key (e.g. `Idempotency-Key` header or `idempotency_key` field).
- [ ] Duplicate requests with the same idempotency key return the original
      response without re-executing the operation.
- [ ] Idempotency keys are stored with a TTL (default: 24 hours).
- [ ] The idempotency key is validated for format and length.

## Safe Retries

- [ ] All payment API calls implement exponential backoff with jitter.
- [ ] Maximum retry count is configurable and bounded (e.g., max 3 retries).
- [ ] Network timeouts are explicitly set — no infinite waits.
- [ ] Retried requests reuse the same idempotency key.

## Partial Failure and Rollback

- [ ] If a multi-step payment operation fails mid-way, all completed steps
      are rolled back (or compensating transactions are issued).
- [ ] Partial failure scenarios are covered by at least one test.
- [ ] The failure response includes which steps succeeded and which failed.

## Duplicate Webhook Detection

- [ ] Incoming webhooks are deduplicated by event ID before processing.
- [ ] Duplicate webhook events return HTTP 200 (not an error) to prevent
      the provider from retrying indefinitely.
- [ ] Webhook signatures are verified before processing the payload.

## Currency and Rounding

- [ ] All monetary amounts are stored and processed in the smallest currency
      unit (e.g. cents for USD, pence for GBP) as integers — never floats.
- [ ] Currency codes follow ISO 4217 (e.g. "USD", "EUR", "GBP").
- [ ] Rounding rules are explicit and consistent (e.g. ROUND_HALF_UP).
- [ ] Mixed-currency operations are rejected with a clear error.

## Security

- [ ] Payment provider API keys are stored in environment variables,
      not in source code or config files.
- [ ] PCI DSS scope is documented — raw card data never touches your servers.
- [ ] All communication with the payment provider uses HTTPS/TLS.

## Logging and Observability

- [ ] Every payment event is logged with: amount, currency, status, provider
      reference ID, and timestamp.
- [ ] No sensitive data (card numbers, CVV, full account numbers) is logged.
- [ ] Failed payments emit a structured error log entry for alerting.

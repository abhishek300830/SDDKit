# Plan: Refund Processing (Demo)

## Summary
Build a `POST /api/orders/{order_id}/refunds` endpoint that validates
order ownership and 30-day eligibility, then delegates to the payment
provider client and dispatches a notification email.

## Architecture Changes

| File | Change |
|---|---|
| `src/refund/handler.py` | New — main request handler |
| `src/refund/eligibility.py` | New — ownership and date checks |
| `src/refund/provider.py` | New — payment provider client |
| `src/refund/notifications.py` | New — email dispatch |
| `tests/test_refund_handler.py` | New — integration tests |
| `tests/test_refund_eligibility.py` | New — unit tests |

## Implementation Steps

### Step 1 — Order ownership validation
Fetch order by ID. Check `order.customer_id == requesting_customer_id`.
Return 404 if not found, 403 if wrong owner. **REQ-001**

### Step 2 — 30-day eligibility check
Compare `order.created_at` against `now - timedelta(days=30)`.
Return HTTP 422 with error body if ineligible. **REQ-002**

### Step 3 — Payment provider refund
Call `provider.create_refund(order_id, amount, idempotency_key=...)`.
Use `order_id + "-refund"` as the idempotency key. **REQ-003**

### Step 4 — Email notification
After successful provider response, dispatch confirmation email
to `order.customer_email`. **REQ-004**

## Risk & Mitigations
- Provider timeout: implement 30-second timeout with retry (max 2 retries).
- Email failure: log and continue — refund is still processed.

# Plan: User Refund Processing

## Summary
Build a refund endpoint that validates the order and applies the 30-day window,
then processes the refund.

## Implementation Steps

### Step 1 — Order validation
Fetch the order by ID and verify it belongs to the requesting user. REQ-001

### Step 2 — Eligibility check
Compare the order creation date against today. Reject if older than 30 days. REQ-002

## NOTE: REQ-003 (payment provider integration) is intentionally omitted here
## to seed a gap for the eval harness.

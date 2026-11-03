# Spec: Refund Processing (Demo)

## Overview
Allow customers to request a full refund for a completed order within 30 days
of purchase. The system validates eligibility, processes the refund via the
payment provider, and notifies the customer by email.

## Requirements

| ID | Requirement | Priority |
|---|---|---|
| REQ-001 | The system must verify the order belongs to the requesting customer. | High |
| REQ-002 | The system must reject refund requests for orders older than 30 days. | High |
| REQ-003 | The system must submit the refund request to the payment provider with an idempotency key. | High |
| REQ-004 | The system must send a confirmation email to the customer after a successful refund. | Medium |

## Out of Scope
- Partial refunds.
- Refunds for digital goods.
- Admin-initiated refunds.

## Open Questions
- None — all resolved.

## Acceptance Criteria
- Valid request results in full refund to original payment method.
- Ineligible request returns HTTP 422 with a clear error message.
- Refund confirmation email sent within 60 seconds.

# Spec: User Refund Processing

## Overview
Allow customers to request a refund for a completed order within 30 days
of purchase. The system must validate eligibility, process the refund via
the payment provider, and notify the customer.

## Requirements

| ID | Requirement | Priority |
|---|---|---|
| REQ-001 | The system must validate that the order exists and belongs to the requesting user. | High |
| REQ-002 | The system must reject refund requests older than 30 days. | High |
| REQ-003 | The system must process the refund via the configured payment provider. | High |

## Out of Scope
- Partial refunds are not supported in this version.
- Refunds for digital goods are handled by a separate policy engine.

## Acceptance Criteria
- A valid refund request results in a full refund within 2 business days.
- An ineligible request returns a clear error message.

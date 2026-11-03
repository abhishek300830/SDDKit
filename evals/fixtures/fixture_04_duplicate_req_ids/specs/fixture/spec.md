# Spec: Webhook Event Processing

## Overview
Process incoming payment webhook events from the payment provider.
Each event must be verified, deduplicated, and dispatched to the
appropriate internal handler.

## Requirements

| ID | Requirement | Priority |
|---|---|---|
| REQ-001 | The system must verify the webhook signature before processing. | High |
| REQ-001 | The system must deduplicate events by event ID. | High |
| REQ-002 | Failed handlers must retry with exponential backoff. | Medium |

## NOTE: REQ-001 appears twice — this is the seeded duplicate ID gap.

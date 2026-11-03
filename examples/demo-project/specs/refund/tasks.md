# Tasks: Refund Processing (Demo)

## Task List

- [x] TASK-01: Implement order ownership validation  <!-- REQ-001 -->
  - File: `src/refund/eligibility.py`
  - Done when: returns 404 for unknown, 403 for wrong owner

- [x] TASK-02: Implement 30-day eligibility check  <!-- REQ-002 -->
  - File: `src/refund/eligibility.py`
  - Done when: returns 422 for orders > 30 days old

- [x] TASK-03: Implement payment provider client  <!-- REQ-003 -->
  - File: `src/refund/provider.py`
  - Done when: calls provider with idempotency key, handles timeout

- [x] TASK-04: Implement email notification  <!-- REQ-004 -->
  - File: `src/refund/notifications.py`
  - Done when: email sent after successful refund

- [x] TASK-05: Write eligibility unit tests  <!-- REQ-001, REQ-002 -->
  - File: `tests/test_refund_eligibility.py`
  - Covers: REQ-001, REQ-002

- [x] TASK-06: Write provider integration tests  <!-- REQ-003 -->
  - File: `tests/test_refund_handler.py`
  - Covers: REQ-003

- [x] TASK-07: Write notification tests  <!-- REQ-004 -->
  - File: `tests/test_refund_handler.py`
  - Covers: REQ-004

## Definition of Done

- [x] All tasks completed
- [x] `sddkit check refund` exits 0
- [x] All tests pass

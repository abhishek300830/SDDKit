# Tasks: Rate Limiting

## Task List

- [ ] TASK-01: Implement rate limit middleware  <!-- REQ-001 -->
  - Done when: 101st request returns 429

- [ ] TASK-02: Implement 429 response with Retry-After  <!-- REQ-002 -->
  - Done when: header present and accurate

- [ ] TASK-03: Implement authenticated user elevated limit  <!-- REQ-003 -->
  - Done when: auth user gets 1000 req/min

- [ ] TASK-04: Redis persistence for counters  <!-- REQ-004 -->
  - Done when: counters survive server restart

- [ ] TASK-05: Write tests for IP rate limiting  <!-- REQ-001, REQ-002 -->
  - Covers: REQ-001, REQ-002

- [ ] TASK-06: Write tests for authenticated limit  <!-- REQ-003 -->
  - Covers: REQ-003

## NOTE: No test task covers REQ-004 (Redis persistence) — this is the seeded gap.

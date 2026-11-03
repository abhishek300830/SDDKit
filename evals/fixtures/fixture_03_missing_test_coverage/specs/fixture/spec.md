# Spec: Rate Limiting for Public API

## Overview
Apply per-IP rate limiting to all public API endpoints to prevent abuse.
Return HTTP 429 with a Retry-After header when the limit is exceeded.

## Requirements

| ID | Requirement | Priority |
|---|---|---|
| REQ-001 | The system must limit each IP to 100 requests per minute on public endpoints. | High |
| REQ-002 | The system must return HTTP 429 with a Retry-After header when the rate limit is exceeded. | High |
| REQ-003 | Authenticated users must have a higher limit of 1000 requests per minute. | Medium |
| REQ-004 | Rate limit counters must persist across server restarts (use Redis or similar). | High |

## Out of Scope
- Per-user rate limiting for internal APIs.
- Geo-based rate limiting.

## Acceptance Criteria
- 101st request from a single IP within a minute returns 429.
- Authenticated user can make 1000 requests before hitting the limit.
- Redis restart does not reset counters mid-window.

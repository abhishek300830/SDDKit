# Plan: Rate Limiting

## Summary
Implement Redis-backed sliding window rate limiting with middleware.

## Steps

### Step 1 — Middleware scaffold
Build a middleware that intercepts every request and applies rate checks. REQ-001, REQ-002

### Step 2 — Redis counter
Store per-IP counters in Redis with a 60-second sliding window. REQ-001, REQ-004

### Step 3 — Authenticated user limit
Detect authenticated users and apply the elevated limit. REQ-003

### Step 4 — 429 response
Return 429 with Retry-After header when limit exceeded. REQ-002

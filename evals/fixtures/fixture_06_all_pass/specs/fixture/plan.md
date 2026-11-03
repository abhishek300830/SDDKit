# Plan: Feature Flag Management

## Summary
Build a CRUD admin API for feature flags backed by a database, with
an in-process LRU cache.

## Steps

### Step 1 — Admin API endpoints
POST/PATCH/GET endpoints for flag management. REQ-001

### Step 2 — Database persistence
Store flags in a `feature_flags` table. REQ-002

### Step 3 — In-memory cache
Cache flag evaluations for 30 seconds with TTL-based eviction. REQ-003

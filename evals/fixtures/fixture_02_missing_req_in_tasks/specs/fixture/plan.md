# Plan: Password Reset

## Summary
Generate a signed token, store it with an expiry, email it to the user,
and invalidate it on first use.

## Implementation Steps

### Step 1 — Token generation
Generate a cryptographically random token, store it with a 60-minute TTL. REQ-001, REQ-002

### Step 2 — Email dispatch
Send the reset link containing the token to the user's email address. REQ-001

### Step 3 — Token validation and invalidation
On use, verify the token, mark it as used, and proceed with the password update. REQ-002, REQ-003

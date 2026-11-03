# Spec: User Authentication — Password Reset

## Overview
Allow registered users to reset their password via a time-limited email link.
The link must expire after 1 hour and be single-use.

## Requirements

| ID | Requirement | Priority |
|---|---|---|
| REQ-001 | The system must send a password reset email with a time-limited token. | High |
| REQ-002 | The reset token must expire after 60 minutes. | High |
| REQ-003 | The reset token must be invalidated after first use. | High |

## Out of Scope
- Social login / OAuth password resets.
- SMS-based reset.

## Acceptance Criteria
- User receives the email within 30 seconds.
- Token cannot be reused after successful reset.
- Expired token returns a clear error.

# Spec: Feature Flag Management

## Overview
Allow engineering teams to toggle feature flags without a code deployment.
Flags must be stored persistently and evaluated per-request.

## Requirements

| ID | Requirement | Priority |
|---|---|---|
| REQ-001 | Operators must be able to enable/disable a feature flag via the admin API. | High |
| REQ-002 | Feature flag state must be persisted to the database. | High |
| REQ-003 | Flag evaluations must be cached in memory for 30 seconds to reduce DB load. | Medium |

## Out of Scope
- Percentage rollouts (A/B testing).
- User-targeting rules.

## Acceptance Criteria
- Toggling a flag is reflected in all new requests within 30 seconds.
- Flag state survives an application restart.

# Spec: Audit Logging Service

## Overview
Record all system events into an immutable audit log.

## Requirements

| ID | Requirement | Priority |
|---|---|---|
| REQ-001 | Log user login attempts with timestamp and IP address. | High |
| REQ-002 | Log permission role changes with actor ID and previous role. | High |
| REQ-003 | Emit alert on 5 consecutive failed login attempts within 10 minutes. | Critical |

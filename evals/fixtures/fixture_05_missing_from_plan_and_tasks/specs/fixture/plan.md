# Plan: Audit Logging Service

## Architecture
Implement an event listener that captures login events and appends them to disk.

## Requirements Coverage
- REQ-001: Captured via FastAPI middleware on `/auth/login`.

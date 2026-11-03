# Demo Project — Refund Processing

This directory shows a complete SDDKit workflow run for the `refund` feature.

## What's here

```
specs/refund/
├── spec.md        ← Requirements with REQ-001…REQ-004
├── plan.md        ← Technical plan citing every REQ-ID
├── tasks.md       ← Task breakdown, all marked [x] done
├── status.json    ← All three stages approved
└── audit.jsonl    ← Real audit log from the demo run
```

## Reproducing this demo

```bash
# 1. Install sddkit
pip install -e .

# 2. Initialise both targets in a fresh directory
mkdir my-project && cd my-project
sddkit init --claude --cursor

# 3. Write a spec
# (in Claude Code, type: /spec)
# Creates: specs/refund/spec.md

# 4. Check traceability (will fail — plan and tasks don't exist yet)
sddkit check refund

# 5. Approve spec
sddkit approve refund spec

# 6. Write plan (/plan), tasks (/tasks)

# 7. Approve plan and tasks
sddkit approve refund plan
sddkit approve refund tasks

# 8. Implement (/implement) — hook blocks writes until gates close

# 9. Check and report
sddkit check refund
sddkit report refund

# 10. Review (/review --pack payments)
```

## Sample audit report

```
Audit Report — feature: refund
==================================================
Total actions : 5
  Allowed     : 4
  Denied      : 1

Blocked actions:
----------------------------------------
  [2025-01-10T10:05:00+00:00]
    Tool   : Write
    Input  : file_path=src/refund/eligibility.py
    Reason : Feature 'refund' approval gates are open...
```

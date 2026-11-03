# SDDKit — Spec-Driven Development Toolkit for Claude Code & Cursor

> **Deterministic checks first, LLM second.**
> Requirement traceability, hook-enforced approval gates, and an audit log
> — for [Claude Code](https://claude.ai/code) and [Cursor](https://cursor.sh).

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What is SDDKit?

SDDKit is a **Python CLI** that sets up a spec-driven development workflow
(spec → plan → tasks → implement → review) for **Claude Code** and **Cursor**
from a single source, and **enforces** the workflow with:

- **Approval gates** — implementation is blocked until spec, plan, and tasks
  are human-approved (in Claude Code via a `PreToolUse` hook; in Cursor via
  pre-commit and CI).
- **Requirement traceability** — every `REQ-ID` is verified to appear in the
  plan, tasks, and tests. Exit code 1 if anything is missing.
- **Audit log** — every agent action is logged to `audit.jsonl` and
  summarisable with `sddkit report`.
- **Eval harness** — `sddkit eval` measures the checker against seeded gaps.

---

## Architecture

```
kit/ (single source: commands, agents, rules, packs)
        │  sddkit init --claude --cursor
        ▼
   generate.py (renderer)
     ├──► .claude/  commands, agents, settings.json (hooks), CLAUDE.md
     └──► .cursor/  commands, rules/*.mdc, AGENTS.md
                │  agent works in the repo
                ▼
   specs/<feature>/  spec.md  plan.md  tasks.md  status.json  audit.jsonl
        │                               │
   ENFORCEMENT                      VALIDATION
   Claude: PreToolUse hook          trace.py (deterministic)
   Cursor: CLI check + pre-commit   validator agent (LLM + domain pack)
        │                               │
        └────────► sddkit report / sddkit eval
```

---

## Quick Start

### 1. Install

```bash
pip install sddkit
# or install from source:
git clone https://github.com/abhishek300830/ssdkit
cd ssdkit
pip install -e .
```

### 2. Initialise in your repo

```bash
cd your-project/

# Both Claude Code and Cursor:
sddkit init --claude --cursor

# Claude Code only:
sddkit init --claude

# Cursor only:
sddkit init --cursor
```

This creates:
- `.claude/commands/` — five slash commands (spec, plan, tasks, implement, review)
- `.claude/agents/validator.md` — LLM validator subagent
- `.claude/hooks/pre_tool_use.py` — approval gate enforcer
- `.claude/settings.json` — hook registration
- `.cursor/commands/` — same five commands for Cursor
- `.cursor/rules/safety.mdc` + `workflow.mdc` — always-apply rules
- `CLAUDE.md` + `AGENTS.md` — project context for agents

### 3. Write a spec

In Claude Code, type `/spec` and describe your feature.  
The agent writes `specs/<feature>/spec.md` with `REQ-001`, `REQ-002`, … IDs.

### 4. Check traceability

```bash
sddkit check <feature>
```

Output:
```
REQ      plan  tasks  tests
REQ-001   ✔     ✔      ✔
REQ-002   ✔     ✔      ✘   <- no test references REQ-002
REQ-003   ✘     ✘      ✘   <- missing from the plan
FAIL: 2 requirements not fully covered
```

### 5. Approve stages

```bash
sddkit approve <feature> spec     # after /spec
sddkit approve <feature> plan     # after /plan
sddkit approve <feature> tasks    # after /tasks
```

The PreToolUse hook (Claude Code) blocks any write to `src/` until all
three stages are approved.

### 6. Implement

Type `/implement` in Claude Code. The hook enforces the gate automatically.

### 7. Review

```bash
/review --pack payments   # applies the payments domain checklist
```

### 8. Audit report

```bash
sddkit report <feature>
```

---

## Claude Code vs Cursor Enforcement

| Mechanism | Claude Code | Cursor |
|---|---|---|
| Real-time gate enforcement | ✔ `PreToolUse` hook denies writes to `src/` | ✘ No equivalent hook |
| CLI traceability check | ✔ `sddkit check` | ✔ `sddkit check` |
| Pre-commit | Optional | **Recommended** — add `sddkit check` to `.pre-commit-config.yaml` |
| CI | ✔ `sddkit eval` in GitHub Actions | ✔ Same |
| Always-apply rules | ✔ `CLAUDE.md` + agent instructions | ✔ `.cursor/rules/workflow.mdc` |

> **Cursor agents:** The workflow rules in `.cursor/rules/workflow.mdc` state
> this difference explicitly so no agent is surprised.

---

## Domain Packs

Domain packs are markdown checklists applied during `/review`.

### Payments pack

```bash
/review --pack payments
```

Covers: idempotency keys, safe retries, partial failure & rollback,
duplicate webhook detection, currency & rounding, PCI hygiene.

---

## Eval Harness

```bash
sddkit eval
```

Runs the deterministic checker against 6 fixture sets (5 seeded gaps + 1 clean false-alarm control):

| Fixture | Seeded gap |
|---|---|
| fixture_01 | REQ-003 missing from plan and tasks |
| fixture_02 | REQ-003 missing from tasks only |
| fixture_03 | REQ-004 has no test coverage |
| fixture_04 | Duplicate REQ-001 in spec |
| fixture_05 | REQ-002 and REQ-003 missing from both plan and tasks |
| fixture_06 | All clean — false-alarm test |

**Real eval results:**
```
Seeded gaps: 5 | Caught: 5 | False alarms: 0
```

> Update this table after running `sddkit eval` on your machine.

---

## Non-functional guarantees

- **NFR-01:** Installs with one command, no cloud account needed.
- **NFR-02:** `check`, `approve`, `report`, and `eval` run with **no LLM or API key**.
- **NFR-03:** Unit tests cover the traceability parser, gate logic, and report builder.
- **NFR-04:** Clear error messages. A failed check names the missing requirement and where it's absent.

---

## Project Layout

```
ssdkit/
├── src/sddkit/   cli.py  generate.py  trace.py  gates.py  audit.py  eval_runner.py
├── kit/          commands/  agents/  hooks/  rules/  packs/
├── examples/demo-project/
├── evals/fixtures/
├── tests/
├── pyproject.toml
└── README.md
```

---

## Post-MVP Roadmap

- Drift detection — a spec change after approval marks the plan stale.
- MCP server exposing `check_coverage` and `get_status` as tools.
- `security.md` domain pack.

---

## License

MIT — see [LICENSE](LICENSE).

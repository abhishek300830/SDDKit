# SDDKit: Requirements & Build Plan

> `sddkit` is a placeholder name. Rename it before publishing, and search GitHub to avoid clashes.

## 1. Overview

**What it is:** A Python CLI that sets up a spec-driven development workflow (spec, plan, tasks, implement, review) for **Claude Code and Cursor** from a single source, and **enforces** the workflow with approval gates, requirement traceability checks, and an audit log.

**Why it is different from GitHub Spec Kit:** it is not just prompt templates. It ships deterministic checks, hook-enforced gates, an audit log, and an eval harness.

**Design rule:** deterministic checks (traceability, gates) are the hard guarantees. The LLM validator agent is an extra reviewer on top, never the only enforcer.

## 2. Goals and Non-Goals

**Goals**
- One source of truth generates setups for both Claude Code and Cursor.
- Requirements are traceable: every `REQ-ID` appears in the plan, tasks, and tests.
- Implementation is blocked until spec, plan, and tasks are human-approved.
- Every agent action is logged and can be summarized in a report.
- The checker is measured with a small eval on seeded gaps.

**Non-Goals (MVP)**
- No web UI.
- No support for tools other than Claude Code and Cursor.
- No drift detection and no MCP server (post-MVP, see section 9).
- No code or prompts taken from any employer's repositories.

## 3. Tech Stack

| Area | Choice |
|---|---|
| Language | Python 3.10+ |
| CLI | `typer` or `argparse` |
| Templates | `jinja2` or plain string templates |
| Packaging | `pyproject.toml`, installable with `pip install -e .` |
| Testing | `pytest` |
| CI | GitHub Actions (run `pytest` and `sddkit eval`) |

Check the current Claude Code and Cursor docs for file formats and hook input/output before generating them. These formats change between releases.

## 4. Functional Requirements

### 4.1 Generator
- **FR-01:** `sddkit init --claude --cursor` generates the setup for the chosen targets in the current repo.
- **FR-02:** Claude Code target creates `.claude/commands/`, `.claude/agents/validator.md`, `.claude/settings.json` (hooks), and `CLAUDE.md`.
- **FR-03:** Cursor target creates `.cursor/commands/`, `.cursor/rules/*.mdc` (always-apply safety and workflow rules).
- **FR-04:** Both targets also create a shared `AGENTS.md`.
- **FR-05:** `init` never overwrites existing files without `--force`.

### 4.2 Workflow commands
- **FR-06:** Five commands: `/spec`, `/plan`, `/tasks`, `/implement`, `/review`.
- **FR-07:** Each command writes into `specs/<feature>/` (`spec.md`, `plan.md`, `tasks.md`).
- **FR-08:** `spec.md` uses requirement IDs in the form `REQ-001`. Plan and tasks must cite these IDs.

### 4.3 Traceability checker (deterministic)
- **FR-09:** `sddkit check <feature>` validates `spec.md` format and that IDs are unique.
- **FR-10:** It reports, per requirement, whether it appears in the plan, tasks, and tests.
- **FR-11:** It exits with a non-zero code if any requirement is not fully covered, so it can run in CI and pre-commit.

Example output:

```
REQ      plan  tasks  tests
REQ-001   ✔     ✔      ✔
REQ-002   ✔     ✔      ✘   <- no test references REQ-002
REQ-003   ✘     ✘      ✘   <- missing from the plan
FAIL: 2 requirements not fully covered
```

### 4.4 Approval gates
- **FR-12:** `sddkit approve <feature> <spec|plan|tasks>` records approval in `specs/<feature>/status.json` with a hash of the file.
- **FR-13:** Approval of a later stage requires the earlier stage to be approved.
- **FR-14:** `/implement` is blocked until spec, plan, and tasks are all approved.
- **FR-15:** Claude Code enforcement is a `PreToolUse` hook that denies source-file writes while gates are open.
- **FR-16:** Cursor has no equivalent hook, so enforcement is `sddkit check` in a pre-commit hook and CI, plus always-apply rules. The README states this difference clearly.

```json
{ "feature": "refund",
  "spec":  { "approved": true,  "hash": "a1f3..." },
  "plan":  { "approved": true,  "hash": "9c2e..." },
  "tasks": { "approved": false, "hash": null } }
```

### 4.5 Safety and audit log
- **FR-17:** The hook appends every tool action to `specs/<feature>/audit.jsonl` (timestamp, tool, input summary, allow/deny).
- **FR-18:** The hook denies commands on a blocklist (for example `rm -rf`, force push, writes outside the repo).
- **FR-19:** `sddkit report <feature>` summarizes actions taken and actions blocked.

### 4.6 Validator agent and domain packs
- **FR-20:** A validator subagent checks each stage against the previous one (does the plan cover the spec, do the tasks match the plan).
- **FR-21:** Domain packs are markdown checklists in `kit/packs/`. Ship one pack: `payments.md` (idempotency keys, safe retries, partial failure and rollback, duplicate webhook detection, currency and rounding).
- **FR-22:** `/review` applies the selected pack, for example `/review --pack payments`.

### 4.7 Eval harness
- **FR-23:** `evals/fixtures/` contains at least 5 spec/plan sets, each with one known seeded gap (missing requirement, untested requirement, and similar).
- **FR-24:** `sddkit eval` runs the checker on all fixtures and prints seeded gaps, gaps caught, and false alarms.
- **FR-25 (optional):** Evaluate the LLM validator by running each fixture several times and reporting catch rate with the number of runs.

Example output:

```
Seeded gaps: 5 | Caught: 5 | False alarms: 0
```

## 5. Non-Functional Requirements

- **NFR-01:** Installs and runs with one command and no cloud account.
- **NFR-02:** `check`, `approve`, `report`, and `eval` run without any LLM or API key.
- **NFR-03:** Unit tests cover the traceability parser, gate logic, and report builder.
- **NFR-04:** Clear error messages. A failed check says which requirement is missing and where.
- **NFR-05:** Everything is built from scratch on sample code, with no employer code, prompts, or workflows.

## 6. Architecture

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

## 7. Repo Structure

```
sddkit/
├── src/sddkit/   cli.py  generate.py  trace.py  gates.py  audit.py
├── kit/          commands/  agents/  hooks/  packs/
├── examples/demo-project/
├── evals/fixtures/
├── tests/
├── .github/workflows/ci.yml
├── pyproject.toml
└── README.md
```

## 8. Milestones and Acceptance Criteria

| # | Milestone | Done when |
|---|---|---|
| 1 | Templates + `generate.py` | `init --claude --cursor` creates both setups in a clean folder |
| 2 | `trace.py` + `check` + tests | The example trace report above is produced, and exit code is non-zero on gaps |
| 3 | `gates.py` + `approve` + Claude hook | A write to `src/` is denied before approval and allowed after |
| 4 | `audit.py` + `report` + demo project | A demo run produces `audit.jsonl` and a readable report |
| 5 | Eval fixtures + `eval` + CI | `sddkit eval` prints real numbers, and CI is green |
| 6 | README + demo GIF | A stranger can install and run the demo in under 5 minutes |

Estimate: one focused weekend (about 10 hours) if you use Claude Code to help, as long as you can explain every file.

## 9. Post-MVP (only after resume is updated)

- Drift detection: a spec change after approval marks the plan stale (the stored hash makes this cheap).
- MCP server exposing `check_coverage` and `get_status` as tools.
- A second domain pack (`security.md`).

## 10. README Must Include

- One-line description and the "deterministic checks first, LLM second" design rule.
- Architecture diagram (section 6).
- Quick start: install, `init`, a full example run.
- Claude Code vs Cursor enforcement differences (FR-16).
- Eval results from your real run, with the date and number of runs.
- Demo GIF.

## 11. Rules Before Adding to the Resume

1. Repo is public with a README and a working install.
2. Every number on the resume comes from your own run of `sddkit eval`.
3. Nothing copied from WatchGuard repos, prompts, or workflows.
4. You can explain why the checker is deterministic and why the gate lives in a hook.
5. Remove "MCP" from the resume stack line if you skip the MCP server.

## 12. Resume Entry (fill in after it works)

```latex
\textbf{SDDKit -- Spec-Driven Development Toolkit for Claude Code \& Cursor} \hfill \textit{\href{YOUR_REPO_URL}{GitHub}} \\
\textit{Python, Claude Code (subagents, hooks, slash commands), Cursor rules}
\begin{itemize}
  \item Built a \textbf{Python CLI} that generates spec-driven workflows (commands, validator agent, safety rules) for \textbf{Claude Code and Cursor} from a single source, with pluggable \textbf{domain checklists}.
  \item Implemented a \textbf{requirement-traceability checker}, \textbf{hook-enforced approval gates}, and a JSONL \textbf{audit log}; validated with an \textbf{eval harness} catching N of M seeded spec gaps.
\end{itemize}
```

Replace `YOUR_REPO_URL`, `N`, and `M` with real values. After it is live, add "AI Agents" back to the resume header and add this Skills line:

```latex
\textbf{Agent Systems:} Claude Code (subagents, hooks, slash commands), Cursor rules, Human-in-the-Loop Workflows
```

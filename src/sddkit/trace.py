"""trace.py — Deterministic requirement traceability checker.

Algorithm
---------
1. Parse ``specs/<feature>/spec.md`` and extract all REQ-NNN IDs.
2. Validate: IDs must match ``REQ-\\d{3}`` and be unique within the spec.
3. Scan ``specs/<feature>/plan.md``, ``tasks.md``, and ``tests/`` for
   every REQ citation.
4. Build a coverage table and render the ASCII report shown in FR-10.
5. Exit code 1 (via CheckResult.passed == False) if any gap exists.

This module has NO LLM dependencies — it is the deterministic enforcer.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Dict

from sddkit.exceptions import TraceError

__all__ = ["check_feature", "CheckResult", "RequirementCoverage", "TraceError"]

# Matches REQ-001 through REQ-999 (exactly 3 digits)
_REQ_PATTERN = re.compile(r"\bREQ-(\d{3})\b")


@dataclass
class RequirementCoverage:
    """Coverage status for a single requirement ID."""

    req_id: str
    in_plan: bool = False
    in_tasks: bool = False
    in_tests: bool = False

    @property
    def fully_covered(self) -> bool:
        """True only when the requirement appears in all three artefacts."""
        return self.in_plan and self.in_tasks and self.in_tests

    def render_row(self) -> str:
        """Return a single table row string."""
        def mark(flag: bool) -> str:
            return "✔" if flag else "✘"

        suffix = ""
        if not self.in_plan:
            suffix += "  <- missing from the plan"
        elif not self.in_tasks:
            suffix += "  <- missing from tasks"
        elif not self.in_tests:
            suffix += "  <- no test references " + self.req_id

        return (
            f"{self.req_id:<10} {mark(self.in_plan):<6} "
            f"{mark(self.in_tasks):<7} {mark(self.in_tests)}{suffix}"
        )


@dataclass
class CheckResult:
    """Aggregated result of a traceability check for a single feature."""

    feature: str
    coverages: List[RequirementCoverage] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True only when there are no parse errors and every REQ is covered."""
        if self.parse_errors:
            return False
        return all(c.fully_covered for c in self.coverages)

    @property
    def gap_count(self) -> int:
        """Number of requirements that are not fully covered."""
        return sum(1 for c in self.coverages if not c.fully_covered)

    def render(self) -> str:
        """Render the human-readable coverage table."""
        lines: List[str] = []

        if self.parse_errors:
            lines.append("PARSE ERRORS:")
            for err in self.parse_errors:
                lines.append(f"  {err}")
            lines.append("")

        if not self.coverages:
            lines.append(f"No REQ-IDs found in specs/{self.feature}/spec.md")
            return "\n".join(lines)

        header = f"{'REQ':<10} {'plan':<6} {'tasks':<7} {'tests'}"
        lines.append(header)
        lines.append("-" * len(header))
        for cov in sorted(self.coverages, key=lambda c: c.req_id):
            lines.append(cov.render_row())

        lines.append("")
        if self.passed:
            lines.append(
                f"PASS: all {len(self.coverages)} requirements fully covered"
            )
        else:
            lines.append(
                f"FAIL: {self.gap_count} requirement(s) not fully covered"
            )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_req_ids(text: str) -> List[str]:
    """Return all REQ-NNN occurrences from *text* in order of appearance."""
    return [f"REQ-{m}" for m in _REQ_PATTERN.findall(text)]


def _read_file(path: Path, label: str) -> str:
    """Read a file and return its text, raising TraceError if missing."""
    if not path.exists():
        raise TraceError(f"Required file not found: {path}  ({label})")
    return path.read_text(encoding="utf-8")


def _scan_directory(directory: Path) -> str:
    """Concatenate text of all files in *directory* (recursive)."""
    if not directory.exists():
        return ""
    parts: List[str] = []
    for p in directory.rglob("*"):
        if p.is_file():
            try:
                parts.append(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_feature(feature: str, repo_root: Path) -> CheckResult:
    """Run the full traceability check for *feature*.

    Parameters
    ----------
    feature:
        Name of the feature folder under ``specs/``.
    repo_root:
        Absolute path to the repository root.

    Returns
    -------
    CheckResult
        The aggregated coverage result. Inspect ``.passed`` for the exit
        decision; call ``.render()`` to get the printable report.

    Raises
    ------
    TraceError
        If ``spec.md`` is missing or cannot be read.
    """
    specs_dir = repo_root / "specs" / feature
    result = CheckResult(feature=feature)

    # 1. Parse spec.md
    spec_path = specs_dir / "spec.md"
    spec_text = _read_file(spec_path, "spec.md")
    all_ids = _extract_req_ids(spec_text)

    if not all_ids:
        # Not a hard error — but there is nothing to check
        return result

    # 2. Validate uniqueness
    seen: Set[str] = set()
    unique_ids: List[str] = []
    for req_id in all_ids:
        if req_id in seen:
            result.parse_errors.append(
                f"Duplicate ID '{req_id}' in spec.md — each REQ-ID must be unique."
            )
        else:
            seen.add(req_id)
            unique_ids.append(req_id)

    # 3. Load artefacts for scanning
    plan_text = ""
    tasks_text = ""
    try:
        plan_text = _read_file(specs_dir / "plan.md", "plan.md")
    except TraceError as exc:
        result.parse_errors.append(str(exc))

    try:
        tasks_text = _read_file(specs_dir / "tasks.md", "tasks.md")
    except TraceError as exc:
        result.parse_errors.append(str(exc))

    tests_text = _scan_directory(repo_root / "tests")

    # 4. Build coverage table
    plan_ids: Set[str] = set(_extract_req_ids(plan_text))
    tasks_ids: Set[str] = set(_extract_req_ids(tasks_text))
    tests_ids: Set[str] = set(_extract_req_ids(tests_text))

    for req_id in unique_ids:
        cov = RequirementCoverage(
            req_id=req_id,
            in_plan=req_id in plan_ids,
            in_tasks=req_id in tasks_ids,
            in_tests=req_id in tests_ids,
        )
        result.coverages.append(cov)

    return result

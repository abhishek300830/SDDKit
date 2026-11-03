"""eval_runner.py — Eval harness for the SDDKit traceability checker.

Discovers all fixture sets under ``evals/fixtures/``, runs the deterministic
checker on each, and compares results against the fixture's ``expected.json``.

Fixture directory layout
------------------------
evals/fixtures/
  fixture_01_missing_req_in_plan/
    spec.md
    plan.md
    tasks.md
    tests/               (optional — simulated test files)
    expected.json        {"pass": false, "errors": ["REQ-003 missing from plan"]}

Eval output
-----------
Seeded gaps: 5 | Caught: 5 | False alarms: 0
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from sddkit.exceptions import EvalError
from sddkit.trace import check_feature, CheckResult

__all__ = ["run_eval", "EvalResult", "FixtureResult", "EvalError"]


@dataclass
class FixtureExpectation:
    """Parsed expected.json for one fixture."""

    should_pass: bool  # True = checker must exit 0; False = checker must fail
    description: str = ""  # Human label for the seeded gap


@dataclass
class FixtureResult:
    """Outcome of running the checker against one fixture."""

    fixture_name: str
    expected_pass: bool
    actual_pass: bool
    description: str

    @property
    def correct(self) -> bool:
        """True when actual outcome matches expected."""
        return self.expected_pass == self.actual_pass

    @property
    def is_false_alarm(self) -> bool:
        """True when checker failed on a fixture that should have passed."""
        return self.expected_pass and not self.actual_pass

    @property
    def is_missed_gap(self) -> bool:
        """True when checker passed on a fixture with a known gap."""
        return not self.expected_pass and self.actual_pass


@dataclass
class EvalResult:
    """Aggregated result of the full eval run."""

    fixtures: List[FixtureResult] = field(default_factory=list)

    @property
    def seeded_gaps(self) -> int:
        """Number of fixtures expected to fail (i.e., have a seeded gap)."""
        return sum(1 for f in self.fixtures if not f.expected_pass)

    @property
    def caught(self) -> int:
        """Number of seeded gaps that the checker correctly caught."""
        return sum(
            1 for f in self.fixtures if not f.expected_pass and not f.actual_pass
        )

    @property
    def false_alarms(self) -> int:
        """Number of clean fixtures that the checker wrongly failed."""
        return sum(1 for f in self.fixtures if f.is_false_alarm)

    def render(self) -> str:
        """Render the eval summary."""
        lines: List[str] = [
            "",
            "SDDKit Eval Results",
            "=" * 40,
        ]
        for fx in self.fixtures:
            icon = "✔" if fx.correct else "✘"
            mode = "PASS" if fx.expected_pass else "FAIL"
            lines.append(f"  {icon}  [{mode}]  {fx.fixture_name}")
            if fx.description:
                lines.append(f"       {fx.description}")
            if fx.is_missed_gap:
                lines.append("       WARNING: seeded gap was NOT caught!")
            if fx.is_false_alarm:
                lines.append("       WARNING: false alarm on a clean fixture!")
        lines.append("")
        lines.append(
            f"Seeded gaps: {self.seeded_gaps} | "
            f"Caught: {self.caught} | "
            f"False alarms: {self.false_alarms}"
        )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_expectation(fixture_dir: Path) -> FixtureExpectation:
    """Parse expected.json in *fixture_dir*."""
    exp_path = fixture_dir / "expected.json"
    if not exp_path.exists():
        raise EvalError(
            f"Fixture '{fixture_dir.name}' is missing expected.json. "
            "Every fixture must declare its expected outcome."
        )
    try:
        data = json.loads(exp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvalError(
            f"Cannot parse expected.json in '{fixture_dir.name}': {exc}"
        ) from exc

    return FixtureExpectation(
        should_pass=bool(data.get("pass", True)),
        description=str(data.get("description", "")),
    )


def _run_fixture(fixture_dir: Path) -> FixtureResult:
    """Run the checker against a single fixture and return the result."""
    expectation = _load_expectation(fixture_dir)

    # The fixture directory itself acts as the repo_root.
    # Feature name is "fixture" — specs/fixture/{spec,plan,tasks}.md
    feature = "fixture"
    repo_root = fixture_dir

    try:
        check_result: CheckResult = check_feature(
            feature=feature, repo_root=repo_root
        )
        actual_pass = check_result.passed
    except Exception:
        actual_pass = False

    return FixtureResult(
        fixture_name=fixture_dir.name,
        expected_pass=expectation.should_pass,
        actual_pass=actual_pass,
        description=expectation.description,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_eval(fixtures_dir: Path, repo_root: Path) -> EvalResult:
    """Run the eval harness against all fixture sets.

    Parameters
    ----------
    fixtures_dir:
        Path to the ``evals/fixtures/`` directory.
    repo_root:
        Absolute path to the repository root (used only for context).

    Returns
    -------
    EvalResult
        Aggregated results. ``result.false_alarms > 0`` signals CI failure.

    Raises
    ------
    EvalError
        If the fixtures directory does not exist or contains no fixtures.
    """
    if not fixtures_dir.exists():
        raise EvalError(
            f"Fixtures directory not found: {fixtures_dir}\n"
            "Run from the repository root or pass --fixtures."
        )

    fixture_dirs = sorted(
        p for p in fixtures_dir.iterdir() if p.is_dir()
    )
    if not fixture_dirs:
        raise EvalError(
            f"No fixture directories found under {fixtures_dir}.\n"
            "Expected subdirectories like fixture_01_missing_req_in_plan/."
        )

    result = EvalResult()
    for fixture_dir in fixture_dirs:
        fx_result = _run_fixture(fixture_dir)
        result.fixtures.append(fx_result)

    return result

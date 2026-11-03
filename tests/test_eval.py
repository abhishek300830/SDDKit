"""test_eval.py — Unit tests for the eval harness (eval_runner.py).

Covers:
  - run_eval discovers and runs all fixtures
  - Seeded gaps are identified and correctly counted
  - Clean fixtures are counted as expected pass
  - Missing fixtures directory raises EvalError
  - Rendering output contains expected summary metrics
"""
from __future__ import annotations

from pathlib import Path
import pytest

from sddkit.eval_runner import run_eval, EvalResult, EvalError


def test_run_eval_against_evals_fixtures(repo: Path) -> None:
    fixtures_dir = Path(__file__).parent.parent / "evals" / "fixtures"
    result = run_eval(fixtures_dir=fixtures_dir, repo_root=fixtures_dir)
    assert isinstance(result, EvalResult)
    assert result.seeded_gaps == 5
    assert result.caught == 5
    assert result.false_alarms == 0
    rendered = result.render()
    assert "Seeded gaps: 5 | Caught: 5 | False alarms: 0" in rendered


def test_run_eval_missing_dir_raises(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist"
    with pytest.raises(EvalError, match="Fixtures directory not found"):
        run_eval(fixtures_dir=non_existent, repo_root=tmp_path)


def test_run_eval_empty_dir_raises(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty_fixtures"
    empty_dir.mkdir()
    with pytest.raises(EvalError, match="No fixture directories found"):
        run_eval(fixtures_dir=empty_dir, repo_root=tmp_path)

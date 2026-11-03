"""test_trace.py — Unit tests for the traceability checker (trace.py).

Covers:
  - Parsing REQ-IDs from spec.md
  - Uniqueness validation (duplicate detection)
  - Coverage table generation
  - Pass/fail determination
  - Missing spec.md raises TraceError
  - Empty spec returns empty result (no crash)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from sddkit.trace import check_feature, CheckResult, TraceError
from tests.conftest import write_spec, write_plan, write_tasks, write_test_file


class TestReqIdParsing:
    """check_feature correctly parses REQ-NNN identifiers."""

    def test_extracts_req_ids_from_spec(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "REQ-001\nREQ-002\nREQ-003")
        write_plan(feature_dir, "REQ-001\nREQ-002\nREQ-003")
        write_tasks(feature_dir, "REQ-001\nREQ-002\nREQ-003")
        write_test_file(repo, "# REQ-001 REQ-002 REQ-003")
        result = check_feature("myfeature", repo)
        req_ids = {c.req_id for c in result.coverages}
        assert req_ids == {"REQ-001", "REQ-002", "REQ-003"}

    def test_ignores_malformed_req_ids(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "REQ-1\nREQ-01\nREQ-1234\nNOT-A-REQ")
        write_plan(feature_dir, "")
        write_tasks(feature_dir, "")
        result = check_feature("myfeature", repo)
        assert result.coverages == []

    def test_empty_spec_returns_empty_result(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "# No requirements here")
        write_plan(feature_dir, "")
        write_tasks(feature_dir, "")
        result = check_feature("myfeature", repo)
        assert result.coverages == []
        assert result.passed is True  # vacuously true (nothing to check)

    def test_missing_spec_raises_trace_error(self, repo: Path) -> None:
        with pytest.raises(TraceError, match="spec.md"):
            check_feature("nonexistent", repo)


class TestDuplicateDetection:
    """Duplicate REQ-IDs in spec.md are caught as parse errors."""

    def test_duplicate_req_id_flagged(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "REQ-001\nREQ-001\nREQ-002")
        write_plan(feature_dir, "REQ-001 REQ-002")
        write_tasks(feature_dir, "REQ-001 REQ-002")
        write_test_file(repo, "# REQ-001 REQ-002")
        result = check_feature("myfeature", repo)
        assert result.passed is False
        assert any("REQ-001" in e for e in result.parse_errors)

    def test_no_false_duplicate_on_unique_ids(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "REQ-001\nREQ-002")
        write_plan(feature_dir, "REQ-001 REQ-002")
        write_tasks(feature_dir, "REQ-001 REQ-002")
        write_test_file(repo, "# REQ-001 REQ-002")
        result = check_feature("myfeature", repo)
        assert result.parse_errors == []


class TestCoverageTable:
    """Coverage is correctly computed for each artefact."""

    def test_all_covered_passes(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "REQ-001\nREQ-002")
        write_plan(feature_dir, "REQ-001 REQ-002")
        write_tasks(feature_dir, "REQ-001 REQ-002")
        write_test_file(repo, "# REQ-001 REQ-002")
        result = check_feature("myfeature", repo)
        assert result.passed is True
        assert result.gap_count == 0

    def test_missing_from_plan_fails(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "REQ-001\nREQ-002")
        write_plan(feature_dir, "REQ-001")  # REQ-002 missing
        write_tasks(feature_dir, "REQ-001 REQ-002")
        write_test_file(repo, "# REQ-001 REQ-002")
        result = check_feature("myfeature", repo)
        assert result.passed is False
        gap = next(c for c in result.coverages if c.req_id == "REQ-002")
        assert gap.in_plan is False
        assert gap.in_tasks is True
        assert gap.in_tests is True

    def test_missing_from_tasks_fails(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "REQ-001\nREQ-002")
        write_plan(feature_dir, "REQ-001 REQ-002")
        write_tasks(feature_dir, "REQ-001")  # REQ-002 missing
        write_test_file(repo, "# REQ-001 REQ-002")
        result = check_feature("myfeature", repo)
        assert result.passed is False
        gap = next(c for c in result.coverages if c.req_id == "REQ-002")
        assert gap.in_tasks is False

    def test_missing_from_tests_fails(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "REQ-001\nREQ-002")
        write_plan(feature_dir, "REQ-001 REQ-002")
        write_tasks(feature_dir, "REQ-001 REQ-002")
        write_test_file(repo, "# REQ-001 only")  # REQ-002 missing
        result = check_feature("myfeature", repo)
        assert result.passed is False
        gap = next(c for c in result.coverages if c.req_id == "REQ-002")
        assert gap.in_tests is False

    def test_missing_plan_file_adds_parse_error(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "REQ-001")
        # plan.md not written intentionally
        write_tasks(feature_dir, "REQ-001")
        result = check_feature("myfeature", repo)
        assert result.passed is False
        assert any("plan.md" in e for e in result.parse_errors)


class TestRenderOutput:
    """CheckResult.render() produces the expected table format."""

    def test_render_pass(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "REQ-001")
        write_plan(feature_dir, "REQ-001")
        write_tasks(feature_dir, "REQ-001")
        write_test_file(repo, "# REQ-001")
        result = check_feature("myfeature", repo)
        output = result.render()
        assert "PASS" in output
        assert "REQ-001" in output
        assert "✔" in output

    def test_render_fail(self, repo: Path, feature_dir: Path) -> None:
        write_spec(feature_dir, "REQ-001\nREQ-002")
        write_plan(feature_dir, "REQ-001")
        write_tasks(feature_dir, "REQ-001")
        write_test_file(repo, "# REQ-001")
        result = check_feature("myfeature", repo)
        output = result.render()
        assert "FAIL" in output
        assert "REQ-002" in output
        assert "✘" in output

"""test_gates.py — Unit tests for the approval gate logic (gates.py).

Covers:
  - Sequential approval (spec → plan → tasks)
  - Prerequisite enforcement
  - SHA-256 hash stored on approval
  - is_gate_open() returns correct values
  - Approving a missing file raises GateError
  - Status persists across load/save cycles
"""
from __future__ import annotations

from pathlib import Path

import pytest

from sddkit.gates import (
    Stage,
    approve_stage,
    is_gate_open,
    load_gate_state,
    GateError,
)


def _write_stage_file(feature_dir: Path, stage: str, content: str = "# content") -> None:
    """Write a spec/plan/tasks file for gate approval."""
    (feature_dir / f"{stage}.md").write_text(content, encoding="utf-8")


class TestSequentialApproval:
    """Approval gates enforce the spec → plan → tasks order."""

    def test_approve_spec_first_succeeds(self, repo: Path, feature_dir: Path) -> None:
        _write_stage_file(feature_dir, "spec")
        status = approve_stage("myfeature", Stage.spec, repo)
        assert status.approved is True
        assert status.file_hash is not None
        assert len(status.file_hash) == 64  # full SHA-256 hex

    def test_approve_plan_without_spec_raises(self, repo: Path, feature_dir: Path) -> None:
        _write_stage_file(feature_dir, "spec")
        _write_stage_file(feature_dir, "plan")
        with pytest.raises(GateError, match="'spec' must be approved first"):
            approve_stage("myfeature", Stage.plan, repo)

    def test_approve_tasks_without_plan_raises(self, repo: Path, feature_dir: Path) -> None:
        _write_stage_file(feature_dir, "spec")
        _write_stage_file(feature_dir, "plan")
        _write_stage_file(feature_dir, "tasks")
        approve_stage("myfeature", Stage.spec, repo)
        with pytest.raises(GateError, match="'plan' must be approved first"):
            approve_stage("myfeature", Stage.tasks, repo)

    def test_full_sequential_approval_succeeds(self, repo: Path, feature_dir: Path) -> None:
        for stage_name in ("spec", "plan", "tasks"):
            _write_stage_file(feature_dir, stage_name)
            approve_stage("myfeature", Stage(stage_name), repo)

        state = load_gate_state("myfeature", repo)
        assert state.all_approved is True

    def test_approve_missing_file_raises(self, repo: Path, feature_dir: Path) -> None:
        # spec.md does not exist
        with pytest.raises(GateError, match="spec.md"):
            approve_stage("myfeature", Stage.spec, repo)


class TestGateOpenCheck:
    """is_gate_open() returns True when any stage is unapproved."""

    def test_gate_open_with_no_status_file(self, repo: Path, feature_dir: Path) -> None:
        assert is_gate_open("myfeature", repo) is True

    def test_gate_open_after_partial_approval(self, repo: Path, feature_dir: Path) -> None:
        _write_stage_file(feature_dir, "spec")
        approve_stage("myfeature", Stage.spec, repo)
        assert is_gate_open("myfeature", repo) is True

    def test_gate_closed_after_all_approved(self, repo: Path, feature_dir: Path) -> None:
        for stage_name in ("spec", "plan", "tasks"):
            _write_stage_file(feature_dir, stage_name)
            approve_stage("myfeature", Stage(stage_name), repo)
        assert is_gate_open("myfeature", repo) is False


class TestStatusPersistence:
    """Approval status is correctly persisted to and loaded from status.json."""

    def test_status_json_written(self, repo: Path, feature_dir: Path) -> None:
        _write_stage_file(feature_dir, "spec")
        approve_stage("myfeature", Stage.spec, repo)
        status_path = feature_dir / "status.json"
        assert status_path.exists()

    def test_status_json_schema(self, repo: Path, feature_dir: Path) -> None:
        import json
        _write_stage_file(feature_dir, "spec")
        approve_stage("myfeature", Stage.spec, repo)
        data = json.loads((feature_dir / "status.json").read_text())
        assert data["feature"] == "myfeature"
        assert data["spec"]["approved"] is True
        assert data["plan"]["approved"] is False
        assert data["tasks"]["approved"] is False

    def test_load_returns_empty_state_if_no_file(self, repo: Path) -> None:
        state = load_gate_state("nonexistent", repo)
        assert state.all_approved is False

    def test_hash_prefix_is_8_chars(self, repo: Path, feature_dir: Path) -> None:
        _write_stage_file(feature_dir, "spec")
        status = approve_stage("myfeature", Stage.spec, repo)
        assert len(status.hash_prefix) == 8

    def test_hash_changes_when_file_changes(self, repo: Path, feature_dir: Path) -> None:
        _write_stage_file(feature_dir, "spec", "version 1")
        status1 = approve_stage("myfeature", Stage.spec, repo)
        # Modify the file and re-approve (spec is already approved — use force logic)
        (feature_dir / "spec.md").write_text("version 2", encoding="utf-8")
        # Re-approve by manipulating status (simulating --force scenario)
        state = load_gate_state("myfeature", repo)
        state.stages["spec"].approved = False
        from sddkit.gates import _save_state
        _save_state(state, repo)
        status2 = approve_stage("myfeature", Stage.spec, repo)
        assert status1.file_hash != status2.file_hash

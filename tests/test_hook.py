"""test_hook.py — Integration and unit tests for the PreToolUse Claude Code hook.

Verifies:
  - Blocklisted bash commands (rm -rf, git push --force) are denied.
  - Normal bash commands are allowed.
  - Source writes to src/ are denied when approval gates are open.
  - Source writes to src/ are allowed when all stages (spec, plan, tasks) are approved.
  - Writes to specs/ or docs are allowed even when gates are open.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from sddkit.gates import Stage, approve_stage
from sddkit.generate import generate_targets


@pytest.fixture
def repo_with_hook(tmp_path: Path) -> Path:
    """Create a temporary repository with the Claude hook initialized."""
    # Create git marker and pyproject.toml
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    generate_targets(repo_root=tmp_path, claude=True, cursor=False, force=True)
    return tmp_path


def run_hook(repo: Path, payload: dict) -> tuple[int, dict | None, str]:
    """Execute pre_tool_use.py with JSON payload on stdin."""
    hook_script = repo / ".claude" / "hooks" / "pre_tool_use.py"
    proc = subprocess.run(
        [sys.executable, str(hook_script)],
        cwd=str(repo),
        input=json.dumps(payload),
        text=True,
        capture_output=True,
    )
    stdout_json = None
    if proc.stdout.strip():
        try:
            stdout_json = json.loads(proc.stdout)
        except Exception:
            pass
    return proc.returncode, stdout_json, proc.stderr


class TestHookBlocklist:
    def test_blocklist_rm_rf(self, repo_with_hook: Path) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /some/dir"},
        }
        ret, out, _ = run_hook(repo_with_hook, payload)
        assert ret == 0
        assert out is not None
        decision = out.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision == "deny"
        assert "Destructive recursive delete is blocked" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_blocklist_git_force_push(self, repo_with_hook: Path) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push --force origin main"},
        }
        ret, out, _ = run_hook(repo_with_hook, payload)
        assert ret == 0
        assert out is not None
        decision = out.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision == "deny"
        assert "Force push is blocked" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_allowed_bash_command(self, repo_with_hook: Path) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "pytest tests/"},
        }
        ret, out, _ = run_hook(repo_with_hook, payload)
        assert ret == 0
        assert out is None  # Allowed produces no deny JSON


class TestHookGateEnforcement:
    def test_write_to_source_denied_when_no_feature_approved(self, repo_with_hook: Path) -> None:
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": "src/app.py"},
        }
        ret, out, _ = run_hook(repo_with_hook, payload)
        assert ret == 0
        assert out is not None
        decision = out.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision == "deny"

    def test_write_to_source_denied_when_only_spec_approved(self, repo_with_hook: Path) -> None:
        feature_dir = repo_with_hook / "specs" / "feature1"
        feature_dir.mkdir(parents=True)
        (feature_dir / "spec.md").write_text("# Spec\n| ID | Requirement |\n| REQ-001 | Test |", encoding="utf-8")
        approve_stage("feature1", Stage.spec, repo_with_hook)

        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": "src/app.py"},
        }
        ret, out, _ = run_hook(repo_with_hook, payload)
        assert ret == 0
        assert out is not None
        decision = out.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision == "deny"
        assert "approval gates are open" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_write_to_source_allowed_when_all_stages_approved(self, repo_with_hook: Path) -> None:
        feature_dir = repo_with_hook / "specs" / "feature1"
        feature_dir.mkdir(parents=True)
        (feature_dir / "spec.md").write_text("# Spec", encoding="utf-8")
        (feature_dir / "plan.md").write_text("# Plan", encoding="utf-8")
        (feature_dir / "tasks.md").write_text("# Tasks", encoding="utf-8")
        approve_stage("feature1", Stage.spec, repo_with_hook)
        approve_stage("feature1", Stage.plan, repo_with_hook)
        approve_stage("feature1", Stage.tasks, repo_with_hook)

        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": "src/app.py"},
        }
        ret, out, _ = run_hook(repo_with_hook, payload)
        assert ret == 0
        assert out is None  # Allowed

    def test_write_to_non_source_allowed_even_if_gate_open(self, repo_with_hook: Path) -> None:
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": "specs/feature1/spec.md"},
        }
        ret, out, _ = run_hook(repo_with_hook, payload)
        assert ret == 0
        assert out is None  # Allowed

"""test_cli.py — Integration tests for CLI commands.

Covers:
  - sddkit --help and --version
  - sddkit init with and without targets
  - sddkit check (success and failure modes)
  - sddkit approve (sequential stages)
  - sddkit report
  - sddkit eval
"""
from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner

from sddkit.cli import app

runner = CliRunner()


def test_cli_version() -> None:
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "sddkit 0.1.0" in res.stdout


def test_cli_help() -> None:
    res = runner.invoke(app, ["--help"])
    assert res.exit_code == 0
    assert "Spec-Driven Development Toolkit" in res.stdout


def test_cli_init_no_targets(tmp_path: Path) -> None:
    res = runner.invoke(app, ["init", "--repo", str(tmp_path)])
    assert res.exit_code != 0
    assert "specify at least one target" in res.stdout.lower()


def test_cli_init_both(tmp_path: Path) -> None:
    res = runner.invoke(app, ["init", "--claude", "--cursor", "--repo", str(tmp_path)])
    assert res.exit_code == 0
    assert ".claude/commands/spec.md" in res.stdout
    assert ".cursor/commands/spec.md" in res.stdout


def test_cli_check_and_approve_workflow(tmp_path: Path) -> None:
    feature_dir = tmp_path / "specs" / "widget"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n\n| ID | Req |\n| REQ-001 | A |", encoding="utf-8")
    (feature_dir / "plan.md").write_text("# Plan\n- REQ-001: implemented", encoding="utf-8")
    (feature_dir / "tasks.md").write_text("# Tasks\n- [ ] TASK-01 <!-- REQ-001 -->", encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_widget.py").write_text("def test_widget():\n    '''REQ-001'''\n    pass", encoding="utf-8")

    # Check passes
    res = runner.invoke(app, ["check", "widget", "--repo", str(tmp_path)])
    assert res.exit_code == 0
    assert "PASS" in res.stdout

    # Approve stages sequentially
    res = runner.invoke(app, ["approve", "widget", "spec", "--repo", str(tmp_path)])
    assert res.exit_code == 0
    assert "widget/spec approved" in res.stdout

    res = runner.invoke(app, ["approve", "widget", "plan", "--repo", str(tmp_path)])
    assert res.exit_code == 0
    assert "widget/plan approved" in res.stdout

    res = runner.invoke(app, ["approve", "widget", "tasks", "--repo", str(tmp_path)])
    assert res.exit_code == 0
    assert "widget/tasks approved" in res.stdout


def test_cli_report_empty(tmp_path: Path) -> None:
    res = runner.invoke(app, ["report", "unknown", "--repo", str(tmp_path)])
    assert res.exit_code == 0
    assert "empty or does not exist" in res.stdout


def test_cli_eval() -> None:
    res = runner.invoke(app, ["eval"])
    assert res.exit_code == 0
    assert "Seeded gaps: 5 | Caught: 5 | False alarms: 0" in res.stdout

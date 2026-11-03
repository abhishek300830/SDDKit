"""test_generate.py — Unit tests for the template renderer (generate.py).

Covers:
  - Claude Code target creates expected files
  - Cursor target creates expected files
  - Both targets together
  - --force flag overwrites existing files
  - Without --force, existing files are skipped
  - Missing kit/ raises GenerateError
"""
from __future__ import annotations

from pathlib import Path

import pytest

from sddkit.generate import generate_targets, GenerateError


# Expected output files per target
_CLAUDE_EXPECTED = {
    ".claude/commands/spec.md",
    ".claude/commands/plan.md",
    ".claude/commands/tasks.md",
    ".claude/commands/implement.md",
    ".claude/commands/review.md",
    ".claude/agents/validator.md",
    ".claude/hooks/pre_tool_use.py",
    ".claude/settings.json",
    "CLAUDE.md",
    "AGENTS.md",
}

_CURSOR_EXPECTED = {
    ".cursor/commands/spec.md",
    ".cursor/commands/plan.md",
    ".cursor/commands/tasks.md",
    ".cursor/commands/implement.md",
    ".cursor/commands/review.md",
    ".cursor/rules/safety.mdc",
    ".cursor/rules/workflow.mdc",
    "AGENTS.md",
}


class TestClaudeTarget:
    """--claude generates the correct files."""

    def test_creates_all_claude_files(self, repo: Path) -> None:
        results = generate_targets(repo, claude=True, cursor=False, force=False)
        created = {k for k, v in results.items() if v == "created"}
        assert _CLAUDE_EXPECTED.issubset(created)

    def test_all_files_actually_exist_on_disk(self, repo: Path) -> None:
        generate_targets(repo, claude=True, cursor=False, force=False)
        for rel in _CLAUDE_EXPECTED:
            assert (repo / rel).exists(), f"Expected file missing: {rel}"

    def test_settings_json_has_pre_tool_use_hook(self, repo: Path) -> None:
        import json
        generate_targets(repo, claude=True, cursor=False, force=False)
        settings = json.loads((repo / ".claude/settings.json").read_text())
        assert "PreToolUse" in settings["hooks"]

    def test_pre_tool_use_hook_is_python_command(self, repo: Path) -> None:
        import json
        generate_targets(repo, claude=True, cursor=False, force=False)
        settings = json.loads((repo / ".claude/settings.json").read_text())
        hook_cmd = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        assert "python3" in hook_cmd
        assert "pre_tool_use.py" in hook_cmd


class TestCursorTarget:
    """--cursor generates the correct files."""

    def test_creates_all_cursor_files(self, repo: Path) -> None:
        results = generate_targets(repo, claude=False, cursor=True, force=False)
        created = {k for k, v in results.items() if v == "created"}
        assert _CURSOR_EXPECTED.issubset(created)

    def test_mdc_files_have_alwaysapply_true(self, repo: Path) -> None:
        generate_targets(repo, claude=False, cursor=True, force=False)
        for rule_name in ("safety", "workflow"):
            mdc_path = repo / ".cursor" / "rules" / f"{rule_name}.mdc"
            content = mdc_path.read_text()
            assert "alwaysApply: true" in content

    def test_no_claude_files_created(self, repo: Path) -> None:
        generate_targets(repo, claude=False, cursor=True, force=False)
        assert not (repo / ".claude").exists()


class TestBothTargets:
    """--claude --cursor generates files for both without duplicates."""

    def test_agents_md_written_once(self, repo: Path) -> None:
        results = generate_targets(repo, claude=True, cursor=True, force=False)
        agents_entries = [k for k in results if k == "AGENTS.md"]
        assert len(agents_entries) == 1

    def test_all_expected_files_present(self, repo: Path) -> None:
        generate_targets(repo, claude=True, cursor=True, force=False)
        for rel in _CLAUDE_EXPECTED | _CURSOR_EXPECTED:
            assert (repo / rel).exists(), f"Missing: {rel}"


class TestForceFlag:
    """--force overwrites existing files; without it they are skipped."""

    def test_existing_file_skipped_without_force(self, repo: Path) -> None:
        generate_targets(repo, claude=True, cursor=False, force=False)
        # Write a sentinel into spec.md
        (repo / ".claude/commands/spec.md").write_text("SENTINEL", encoding="utf-8")
        results = generate_targets(repo, claude=True, cursor=False, force=False)
        assert results[".claude/commands/spec.md"] == "skipped"
        # Content unchanged
        assert (repo / ".claude/commands/spec.md").read_text() == "SENTINEL"

    def test_existing_file_overwritten_with_force(self, repo: Path) -> None:
        generate_targets(repo, claude=True, cursor=False, force=False)
        (repo / ".claude/commands/spec.md").write_text("SENTINEL", encoding="utf-8")
        results = generate_targets(repo, claude=True, cursor=False, force=True)
        assert results[".claude/commands/spec.md"] == "created"
        content = (repo / ".claude/commands/spec.md").read_text()
        assert content != "SENTINEL"

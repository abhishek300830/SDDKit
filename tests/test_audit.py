"""test_audit.py — Unit tests for the audit log writer and report builder.

Covers:
  - log_action appends valid JSONL records
  - Multiple calls produce multiple lines
  - build_report produces correct counts
  - build_report handles empty/missing log
  - Malformed JSONL raises AuditError
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sddkit.audit import log_action, build_report, AuditError


class TestLogAction:
    """log_action writes well-formed JSONL records."""

    def test_creates_audit_jsonl(self, repo: Path, feature_dir: Path) -> None:
        log_action("myfeature", "Write", "file_path=src/app.py", True, "", repo)
        log_path = feature_dir / "audit.jsonl"
        assert log_path.exists()

    def test_record_is_valid_json(self, repo: Path, feature_dir: Path) -> None:
        log_action("myfeature", "Write", "file_path=src/app.py", True, "", repo)
        log_path = feature_dir / "audit.jsonl"
        line = log_path.read_text().strip()
        record = json.loads(line)
        assert record["tool"] == "Write"
        assert record["allowed"] is True
        assert "timestamp" in record

    def test_multiple_calls_append(self, repo: Path, feature_dir: Path) -> None:
        log_action("myfeature", "Write", "src/a.py", True, "", repo)
        log_action("myfeature", "Bash", "rm -rf", False, "Blocked", repo)
        log_action("myfeature", "Edit", "src/b.py", True, "", repo)
        log_path = feature_dir / "audit.jsonl"
        lines = [l for l in log_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 3

    def test_denied_action_stores_reason(self, repo: Path, feature_dir: Path) -> None:
        log_action("myfeature", "Bash", "rm -rf /", False, "Destructive delete blocked", repo)
        log_path = feature_dir / "audit.jsonl"
        record = json.loads(log_path.read_text().strip())
        assert record["allowed"] is False
        assert "Destructive delete blocked" in record["reason"]

    def test_creates_parent_directories(self, repo: Path) -> None:
        """log_action creates specs/<feature>/ if it doesn't exist."""
        log_action("brand_new_feature", "Write", "src/x.py", True, "", repo)
        log_path = repo / "specs" / "brand_new_feature" / "audit.jsonl"
        assert log_path.exists()


class TestBuildReport:
    """build_report produces the correct summary text."""

    def test_report_shows_allowed_count(self, repo: Path, feature_dir: Path) -> None:
        log_action("myfeature", "Write", "src/a.py", True, "", repo)
        log_action("myfeature", "Write", "src/b.py", True, "", repo)
        report = build_report("myfeature", repo)
        assert "Allowed     : 2" in report

    def test_report_shows_denied_count(self, repo: Path, feature_dir: Path) -> None:
        log_action("myfeature", "Bash", "rm -rf", False, "Blocked", repo)
        report = build_report("myfeature", repo)
        assert "Denied      : 1" in report

    def test_report_lists_blocked_actions(self, repo: Path, feature_dir: Path) -> None:
        log_action("myfeature", "Bash", "rm -rf /var", False, "Destructive delete", repo)
        report = build_report("myfeature", repo)
        assert "rm -rf /var" in report
        assert "Destructive delete" in report

    def test_empty_log_returns_informative_message(self, repo: Path, feature_dir: Path) -> None:
        report = build_report("myfeature", repo)
        assert "empty" in report.lower() or "does not exist" in report.lower()

    def test_missing_feature_returns_informative_message(self, repo: Path) -> None:
        report = build_report("nonexistent", repo)
        assert "nonexistent" in report

    def test_malformed_jsonl_raises_audit_error(self, repo: Path, feature_dir: Path) -> None:
        log_path = feature_dir / "audit.jsonl"
        log_path.write_text("not json\n", encoding="utf-8")
        with pytest.raises(AuditError, match="Malformed JSON"):
            build_report("myfeature", repo)

    def test_total_count_is_sum(self, repo: Path, feature_dir: Path) -> None:
        log_action("myfeature", "Write", "src/a.py", True, "", repo)
        log_action("myfeature", "Bash", "bad cmd", False, "blocked", repo)
        log_action("myfeature", "Edit", "src/b.py", True, "", repo)
        report = build_report("myfeature", repo)
        assert "Total actions : 3" in report

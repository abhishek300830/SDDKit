"""audit.py — JSONL audit log writer and report builder.

Every Claude Code hook action is appended to ``specs/<feature>/audit.jsonl``
as a single JSON object per line. The ``report`` command reads this file and
summarises allowed vs denied actions.

JSONL record schema
-------------------
{
  "timestamp": "2025-01-01T12:00:00+00:00",
  "feature": "refund",
  "tool": "Write",
  "input_summary": "file_path=src/payments.py",
  "allowed": true,
  "reason": ""
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sddkit.exceptions import AuditError

__all__ = ["log_action", "build_report", "AuditRecord", "AuditError"]


@dataclass
class AuditRecord:
    """A single audit log entry."""

    timestamp: str
    feature: str
    tool: str
    input_summary: str
    allowed: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp,
            "feature": self.feature,
            "tool": self.tool,
            "input_summary": self.input_summary,
            "allowed": self.allowed,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "AuditRecord":
        return cls(
            timestamp=str(data.get("timestamp", "")),
            feature=str(data.get("feature", "")),
            tool=str(data.get("tool", "")),
            input_summary=str(data.get("input_summary", "")),
            allowed=bool(data.get("allowed", True)),
            reason=str(data.get("reason", "")),
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _audit_path(feature: str, repo_root: Path) -> Path:
    return repo_root / "specs" / feature / "audit.jsonl"


def _load_records(feature: str, repo_root: Path) -> List[AuditRecord]:
    """Parse audit.jsonl and return all records."""
    path = _audit_path(feature, repo_root)
    if not path.exists():
        return []
    records: List[AuditRecord] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            records.append(AuditRecord.from_dict(data))
        except json.JSONDecodeError as exc:
            raise AuditError(
                f"Malformed JSON on line {lineno} of "
                f"specs/{feature}/audit.jsonl: {exc}"
            ) from exc
    return records


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_action(
    feature: str,
    tool: str,
    input_summary: str,
    allowed: bool,
    reason: str = "",
    repo_root: Optional[Path] = None,
) -> None:
    """Append one action record to the audit log.

    Parameters
    ----------
    feature:
        Feature name (folder under specs/).
    tool:
        Claude Code tool name (e.g. "Write", "Bash").
    input_summary:
        Short description of the tool input (e.g. "file_path=src/app.py").
    allowed:
        True if the action was permitted; False if it was denied.
    reason:
        Human-readable reason for the decision (empty string if allowed).
    repo_root:
        Repository root. Defaults to the current working directory.

    Raises
    ------
    AuditError
        If the audit log cannot be written.
    """
    if repo_root is None:
        repo_root = Path.cwd()

    record = AuditRecord(
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
        feature=feature,
        tool=tool,
        input_summary=input_summary,
        allowed=allowed,
        reason=reason,
    )

    path = _audit_path(feature, repo_root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict()) + "\n")
    except OSError as exc:
        raise AuditError(f"Cannot write audit log: {exc}") from exc


def build_report(feature: str, repo_root: Path) -> str:
    """Build a human-readable summary of the audit log for *feature*.

    Parameters
    ----------
    feature:
        Feature name (folder under specs/).
    repo_root:
        Absolute path to the repository root.

    Returns
    -------
    str
        Formatted text report.

    Raises
    ------
    AuditError
        If the audit log cannot be read.
    """
    records = _load_records(feature, repo_root)

    if not records:
        return (
            f"Audit log for feature '{feature}' is empty or does not exist.\n"
            f"Expected at: specs/{feature}/audit.jsonl"
        )

    allowed = [r for r in records if r.allowed]
    denied = [r for r in records if not r.allowed]

    lines: List[str] = [
        f"Audit Report — feature: {feature}",
        "=" * 50,
        f"Total actions : {len(records)}",
        f"  Allowed     : {len(allowed)}",
        f"  Denied      : {len(denied)}",
        "",
    ]

    if denied:
        lines.append("Blocked actions:")
        lines.append("-" * 40)
        for rec in denied:
            lines.append(f"  [{rec.timestamp}]")
            lines.append(f"    Tool   : {rec.tool}")
            lines.append(f"    Input  : {rec.input_summary}")
            lines.append(f"    Reason : {rec.reason}")
            lines.append("")

    if allowed:
        lines.append("Allowed actions (most recent first):")
        lines.append("-" * 40)
        for rec in reversed(allowed[-10:]):  # show last 10
            lines.append(
                f"  [{rec.timestamp}]  {rec.tool}  {rec.input_summary}"
            )

    return "\n".join(lines)

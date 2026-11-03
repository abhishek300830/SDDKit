"""gates.py — Approval gate logic for SDDKit.

Approval is sequential: spec → plan → tasks.
Approving a later stage requires all earlier stages to be approved first.
Each approval stores a SHA-256 hash of the file at the time of approval
so that later drift detection (post-MVP) can detect stale approvals cheaply.

status.json schema
------------------
{
  "feature": "refund",
  "spec":  { "approved": false, "hash": null, "approved_at": null },
  "plan":  { "approved": false, "hash": null, "approved_at": null },
  "tasks": { "approved": false, "hash": null, "approved_at": null }
}
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

from sddkit.exceptions import GateError

__all__ = ["Stage", "ApprovalStatus", "GateState", "approve_stage", "is_gate_open", "load_gate_state", "GateError"]

# Stage ordering — index determines prerequisite chain
_STAGE_ORDER = ["spec", "plan", "tasks"]


class Stage(str, Enum):
    """Valid approval stages, in sequential order."""

    spec = "spec"
    plan = "plan"
    tasks = "tasks"

    @property
    def order_index(self) -> int:
        """Return the zero-based position in the approval chain."""
        return _STAGE_ORDER.index(self.value)

    @property
    def prerequisite(self) -> Optional["Stage"]:
        """Return the stage that must be approved before this one, or None."""
        idx = self.order_index
        if idx == 0:
            return None
        return Stage(_STAGE_ORDER[idx - 1])


@dataclass
class ApprovalStatus:
    """Status of a single stage approval."""

    stage: Stage
    approved: bool
    file_hash: Optional[str]  # full SHA-256 hex digest
    approved_at: Optional[str]  # ISO-8601 UTC timestamp

    @property
    def hash_prefix(self) -> str:
        """Return the first 8 characters of the hash, or '--------'."""
        return self.file_hash[:8] if self.file_hash else "--------"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approved": self.approved,
            "hash": self.file_hash,
            "approved_at": self.approved_at,
        }


@dataclass
class GateState:
    """Full approval state for a feature."""

    feature: str
    stages: Dict[str, ApprovalStatus]

    @property
    def all_approved(self) -> bool:
        """True when spec, plan, and tasks are all approved."""
        return all(s.approved for s in self.stages.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature,
            **{name: status.to_dict() for name, status in self.stages.items()},
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _status_path(feature: str, repo_root: Path) -> Path:
    return repo_root / "specs" / feature / "status.json"


def _hash_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _empty_state(feature: str) -> GateState:
    """Return a fresh, unapproved GateState for *feature*."""
    stages: Dict[str, ApprovalStatus] = {}
    for stage_name in _STAGE_ORDER:
        stages[stage_name] = ApprovalStatus(
            stage=Stage(stage_name),
            approved=False,
            file_hash=None,
            approved_at=None,
        )
    return GateState(feature=feature, stages=stages)


def _parse_state(feature: str, data: Dict[str, Any]) -> GateState:
    """Parse a status.json dict into a GateState."""
    stages: Dict[str, ApprovalStatus] = {}
    for stage_name in _STAGE_ORDER:
        raw = data.get(stage_name, {})
        stages[stage_name] = ApprovalStatus(
            stage=Stage(stage_name),
            approved=bool(raw.get("approved", False)),
            file_hash=raw.get("hash"),
            approved_at=raw.get("approved_at"),
        )
    return GateState(feature=feature, stages=stages)


def _save_state(state: GateState, repo_root: Path) -> None:
    path = _status_path(state.feature, repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_gate_state(feature: str, repo_root: Path) -> GateState:
    """Load the approval state for *feature* from status.json.

    Returns an empty (all unapproved) state if status.json does not exist yet.

    Raises
    ------
    GateError
        If status.json exists but cannot be parsed.
    """
    path = _status_path(feature, repo_root)
    if not path.exists():
        return _empty_state(feature)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise GateError(
            f"Cannot read specs/{feature}/status.json: {exc}"
        ) from exc
    return _parse_state(feature, data)


def is_gate_open(feature: str, repo_root: Path) -> bool:
    """Return True if ANY required stage (spec/plan/tasks) is not yet approved.

    A True result means implementation must be blocked.
    """
    try:
        state = load_gate_state(feature, repo_root)
    except GateError:
        return True  # treat unreadable state as open gate (fail-safe)
    return not state.all_approved


def approve_stage(feature: str, stage: Stage, repo_root: Path) -> ApprovalStatus:
    """Record human approval for *stage* in a feature.

    Parameters
    ----------
    feature:
        Feature folder name under ``specs/``.
    stage:
        The stage to approve (spec, plan, or tasks).
    repo_root:
        Absolute path to the repository root.

    Returns
    -------
    ApprovalStatus
        The updated approval record for the approved stage.

    Raises
    ------
    GateError
        If the prerequisite stage is not yet approved, if the stage file
        is missing, or if status.json cannot be read/written.
    """
    state = load_gate_state(feature, repo_root)

    # Check prerequisite
    prereq = stage.prerequisite
    if prereq is not None:
        prereq_status = state.stages[prereq.value]
        if not prereq_status.approved:
            raise GateError(
                f"Cannot approve '{stage.value}': "
                f"'{prereq.value}' must be approved first."
            )

    # Check that the target file exists
    stage_file = repo_root / "specs" / feature / f"{stage.value}.md"
    if not stage_file.exists():
        raise GateError(
            f"Stage file not found: specs/{feature}/{stage.value}.md\n"
            f"Run /spec (or /plan, /tasks) first to create it."
        )

    # Hash and approve
    file_hash = _hash_file(stage_file)
    now_iso = datetime.now(tz=timezone.utc).isoformat()

    updated = ApprovalStatus(
        stage=stage,
        approved=True,
        file_hash=file_hash,
        approved_at=now_iso,
    )
    state.stages[stage.value] = updated
    _save_state(state, repo_root)

    return updated

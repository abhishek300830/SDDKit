"""conftest.py — Shared pytest fixtures for SDDKit tests.

All tests use tmp_path-based temporary directories to avoid filesystem
pollution between test runs.
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """Return a temporary directory that acts as a repository root.

    Pre-creates the basic structure expected by SDDKit modules:
      - specs/
      - tests/
    """
    (tmp_path / "specs").mkdir()
    (tmp_path / "tests").mkdir()
    return tmp_path


@pytest.fixture()
def feature_dir(repo: Path) -> Path:
    """Return a pre-created specs/myfeature/ directory inside ``repo``."""
    feature = repo / "specs" / "myfeature"
    feature.mkdir(parents=True)
    return feature


def write_spec(feature_dir: Path, content: str) -> Path:
    """Write spec.md to feature_dir and return the path."""
    p = feature_dir / "spec.md"
    p.write_text(content, encoding="utf-8")
    return p


def write_plan(feature_dir: Path, content: str) -> Path:
    p = feature_dir / "plan.md"
    p.write_text(content, encoding="utf-8")
    return p


def write_tasks(feature_dir: Path, content: str) -> Path:
    p = feature_dir / "tasks.md"
    p.write_text(content, encoding="utf-8")
    return p


def write_test_file(repo: Path, content: str, filename: str = "test_feature.py") -> Path:
    p = repo / "tests" / filename
    p.write_text(content, encoding="utf-8")
    return p

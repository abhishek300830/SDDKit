"""generate.py — Template renderer for the SDDKit init command.

Walks the ``kit/`` directory, renders every ``*.j2`` Jinja2 template,
and writes the results into the correct output path inside the target repo.

Output mapping
--------------
Claude Code target  (--claude):
    kit/commands/*.md.j2        →  .claude/commands/*.md
    kit/agents/validator.md.j2  →  .claude/agents/validator.md
    kit/hooks/pre_tool_use.py.j2 → .claude/hooks/pre_tool_use.py
    (inline JSON)               →  .claude/settings.json
    kit/CLAUDE.md.j2            →  CLAUDE.md
    kit/AGENTS.md.j2            →  AGENTS.md

Cursor target       (--cursor):
    kit/commands/*.md.j2        →  .cursor/commands/*.md
    kit/rules/*.mdc.j2          →  .cursor/rules/*.mdc
    kit/AGENTS.md.j2            →  AGENTS.md

Status values in the returned mapping: "created" | "skipped" | "error".
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from sddkit.exceptions import GenerateError

__all__ = ["generate_targets", "GenerateError"]

# Path to the kit/ directory (sibling of src/)
_KIT_DIR = Path(__file__).parent.parent.parent / "kit"

# Jinja2 template context — minimal variables used across templates
_TEMPLATE_CONTEXT: dict[str, str] = {
    "sddkit_version": "0.1.0",
}


def _make_env(kit_dir: Path) -> Environment:
    """Create a strict Jinja2 environment rooted at *kit_dir*."""
    return Environment(
        loader=FileSystemLoader(str(kit_dir)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=False,
    )


def _render(env: Environment, template_path: str, context: dict[str, str]) -> str:
    """Render a Jinja2 template and return the result as a string."""
    tpl = env.get_template(template_path)
    return tpl.render(**context)


def _write(dest: Path, content: str, force: bool) -> str:
    """Write *content* to *dest*, respecting the *force* flag.

    Returns
    -------
    "created"  if the file was written.
    "skipped"  if the file already existed and --force was not set.
    """
    if dest.exists() and not force:
        return "skipped"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return "created"


def _claude_settings_json(repo_root: Path, force: bool) -> tuple[str, str]:
    """Generate .claude/settings.json with PreToolUse hook registration."""
    dest = repo_root / ".claude" / "settings.json"
    settings = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit|Create|Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 .claude/hooks/pre_tool_use.py",
                            "timeout": 10,
                            "statusMessage": "SDDKit: checking approval gates...",
                        }
                    ],
                }
            ]
        }
    }
    content = json.dumps(settings, indent=2) + "\n"
    status = _write(dest, content, force)
    return str(dest.relative_to(repo_root)), status


def generate_targets(
    repo_root: Path,
    claude: bool,
    cursor: bool,
    force: bool = False,
) -> Dict[str, str]:
    """Render and write all workflow files for the selected targets.

    Parameters
    ----------
    repo_root:
        Absolute path to the target repository root.
    claude:
        If True, generate Claude Code setup.
    cursor:
        If True, generate Cursor setup.
    force:
        If True, overwrite existing files.

    Returns
    -------
    Dict mapping relative output path → status ("created" | "skipped").

    Raises
    ------
    GenerateError
        If the kit directory is missing or a template fails to render.
    """
    if not _KIT_DIR.exists():
        raise GenerateError(
            f"kit/ directory not found at {_KIT_DIR}. "
            "Ensure sddkit is installed correctly."
        )

    env = _make_env(_KIT_DIR)
    ctx = dict(_TEMPLATE_CONTEXT)
    results: Dict[str, str] = {}

    def _process(template_rel: str, dest: Path) -> None:
        """Render template_rel and write to dest; record result."""
        try:
            content = _render(env, template_rel, ctx)
        except Exception as exc:
            raise GenerateError(
                f"Failed to render template '{template_rel}': {exc}"
            ) from exc
        status = _write(dest, content, force)
        results[str(dest.relative_to(repo_root))] = status

    # ------------------------------------------------------------------ #
    # Claude Code target                                                    #
    # ------------------------------------------------------------------ #
    if claude:
        commands_out = repo_root / ".claude" / "commands"
        for cmd in ["spec", "plan", "tasks", "implement", "review"]:
            _process(f"commands/{cmd}.md.j2", commands_out / f"{cmd}.md")

        _process(
            "agents/validator.md.j2",
            repo_root / ".claude" / "agents" / "validator.md",
        )
        _process(
            "hooks/pre_tool_use.py.j2",
            repo_root / ".claude" / "hooks" / "pre_tool_use.py",
        )
        # settings.json is generated inline (not from a template)
        rel, status = _claude_settings_json(repo_root, force)
        results[rel] = status

        _process("CLAUDE.md.j2", repo_root / "CLAUDE.md")
        _process("AGENTS.md.j2", repo_root / "AGENTS.md")

    # ------------------------------------------------------------------ #
    # Cursor target                                                         #
    # ------------------------------------------------------------------ #
    if cursor:
        commands_out = repo_root / ".cursor" / "commands"
        for cmd in ["spec", "plan", "tasks", "implement", "review"]:
            _process(f"commands/{cmd}.md.j2", commands_out / f"{cmd}.md")

        rules_out = repo_root / ".cursor" / "rules"
        for rule in ["safety", "workflow"]:
            _process(f"rules/{rule}.mdc.j2", rules_out / f"{rule}.mdc")

        # AGENTS.md is shared — only write once even if both targets selected
        agents_dest = repo_root / "AGENTS.md"
        if str(agents_dest.relative_to(repo_root)) not in results:
            _process("AGENTS.md.j2", agents_dest)

    return results

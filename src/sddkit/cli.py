"""SDDKit CLI — entry point for all sddkit commands.

Commands
--------
sddkit init     Generate Claude Code / Cursor workflow files.
sddkit check    Run deterministic traceability check on a feature.
sddkit approve  Record human approval for a spec stage.
sddkit report   Summarise the audit log for a feature.
sddkit eval     Run the eval harness against all fixture sets.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from sddkit import __version__
from sddkit.generate import generate_targets, GenerateError
from sddkit.trace import check_feature, CheckResult
from sddkit.gates import approve_stage, GateError, Stage
from sddkit.audit import build_report, AuditError
from sddkit.eval_runner import run_eval

__all__ = ["app"]

app = typer.Typer(
    name="sddkit",
    help="Spec-Driven Development Toolkit for Claude Code and Cursor.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"sddkit {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the installed version and exit.",
    ),
) -> None:
    """SDDKit — deterministic checks first, LLM second."""


# ---------------------------------------------------------------------------
# sddkit init
# ---------------------------------------------------------------------------

@app.command("init")
def cmd_init(
    claude: bool = typer.Option(False, "--claude", help="Generate Claude Code setup."),
    cursor: bool = typer.Option(False, "--cursor", help="Generate Cursor setup."),
    force: bool = typer.Option(
        False, "--force", help="Overwrite existing files."
    ),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Target repository root (default: current directory).",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Generate Claude Code and/or Cursor workflow files in the target repo."""
    if not claude and not cursor:
        typer.echo(
            "Error: specify at least one target: --claude, --cursor, or both.",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        results = generate_targets(
            repo_root=repo.resolve(),
            claude=claude,
            cursor=cursor,
            force=force,
        )
    except GenerateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    for path, status in results.items():
        icon = "✔" if status == "created" else ("↷" if status == "skipped" else "!")
        typer.echo(f"  {icon}  {path}  [{status}]")

    typer.echo("\nDone. Run `sddkit check <feature>` after writing your spec.")


# ---------------------------------------------------------------------------
# sddkit check
# ---------------------------------------------------------------------------

@app.command("check")
def cmd_check(
    feature: str = typer.Argument(..., help="Feature name (folder under specs/)."),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository root.",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Check requirement traceability for a feature.

    Exits with code 1 if any requirement is not fully covered.
    """
    result: CheckResult = check_feature(feature=feature, repo_root=repo.resolve())
    typer.echo(result.render())
    if not result.passed:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# sddkit approve
# ---------------------------------------------------------------------------

@app.command("approve")
def cmd_approve(
    feature: str = typer.Argument(..., help="Feature name (folder under specs/)."),
    stage: Stage = typer.Argument(
        ..., help="Stage to approve: spec, plan, or tasks."
    ),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository root.",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Record human approval for a spec stage.

    Approval is sequential: spec → plan → tasks.
    """
    try:
        status = approve_stage(
            feature=feature, stage=stage, repo_root=repo.resolve()
        )
    except GateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"  ✔  {feature}/{stage.value} approved  (hash: {status.hash_prefix})")
    typer.echo(f"     Recorded in specs/{feature}/status.json")


# ---------------------------------------------------------------------------
# sddkit report
# ---------------------------------------------------------------------------

@app.command("report")
def cmd_report(
    feature: str = typer.Argument(..., help="Feature name (folder under specs/)."),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository root.",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Print an audit log summary for a feature."""
    try:
        report_text = build_report(feature=feature, repo_root=repo.resolve())
    except AuditError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(report_text)


# ---------------------------------------------------------------------------
# sddkit eval
# ---------------------------------------------------------------------------

@app.command("eval")
def cmd_eval(
    fixtures_dir: Path = typer.Option(
        Path("evals/fixtures"),
        "--fixtures",
        help="Path to fixtures directory.",
    ),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository root.",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Run the eval harness against all fixture sets and report catch rate."""
    results = run_eval(
        fixtures_dir=(repo.resolve() / fixtures_dir).resolve(),
        repo_root=repo.resolve(),
    )
    typer.echo(results.render())
    if results.false_alarms > 0:
        raise typer.Exit(code=1)

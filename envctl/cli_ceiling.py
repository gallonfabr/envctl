"""CLI commands for managing per-project profile ceilings."""

from __future__ import annotations

import click

from envctl.ceiling import (
    CeilingError,
    set_ceiling,
    remove_ceiling,
    get_ceiling,
    ceiling_status,
)


@click.group("ceiling")
def ceiling_cmd() -> None:
    """Manage profile count ceilings for projects."""


@ceiling_cmd.command("set")
@click.argument("project")
@click.argument("limit", type=int)
def set_cmd(project: str, limit: int) -> None:
    """Set the maximum number of profiles for PROJECT."""
    try:
        set_ceiling(project, limit)
        click.echo(f"Ceiling for '{project}' set to {limit} profile(s).")
    except CeilingError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@ceiling_cmd.command("remove")
@click.argument("project")
def remove_cmd(project: str) -> None:
    """Remove the ceiling constraint for PROJECT."""
    remove_ceiling(project)
    click.echo(f"Ceiling removed for '{project}'.")


@ceiling_cmd.command("show")
@click.argument("project")
def show_cmd(project: str) -> None:
    """Show the current ceiling status for PROJECT."""
    status = ceiling_status(project)
    limit = status["limit"]
    if limit is None:
        click.echo(f"No ceiling set for '{project}'. Used: {status['used']} profile(s).")
    else:
        click.echo(
            f"Project '{project}': {status['used']}/{limit} profile(s) used "
            f"({status['available']} available)."
        )

"""CLI commands for managing retention policies."""

import click
from envctl.retention import (
    RetentionError,
    set_retention,
    get_retention,
    clear_retention,
    apply_retention,
)


@click.group("retention")
def retention_cmd() -> None:
    """Manage profile retention policies."""


@retention_cmd.command("set")
@click.argument("project")
@click.argument("days", type=int)
def set_cmd(project: str, days: int) -> None:
    """Set a retention policy of DAYS days for PROJECT."""
    try:
        set_retention(project, days)
        click.echo(f"Retention policy set: {days} day(s) for project '{project}'.")
    except RetentionError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@retention_cmd.command("show")
@click.argument("project")
def show_cmd(project: str) -> None:
    """Show the retention policy for PROJECT."""
    days = get_retention(project)
    if days is None:
        click.echo(f"No retention policy set for project '{project}'.")
    else:
        click.echo(f"Retention policy for '{project}': {days} day(s).")


@retention_cmd.command("clear")
@click.argument("project")
def clear_cmd(project: str) -> None:
    """Remove the retention policy for PROJECT."""
    clear_retention(project)
    click.echo(f"Retention policy cleared for project '{project}'.")


@retention_cmd.command("apply")
@click.argument("project")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without deleting.")
def apply_cmd(project: str, dry_run: bool) -> None:
    """Apply the retention policy for PROJECT, purging stale profiles."""
    try:
        purged = apply_retention(project, dry_run=dry_run)
        if not purged:
            click.echo("No profiles eligible for purging.")
        else:
            label = "Would purge" if dry_run else "Purged"
            for name in purged:
                click.echo(f"{label}: {name}")
    except RetentionError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

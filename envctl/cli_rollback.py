"""CLI commands for rolling back applied profiles."""

import click
from envctl.rollback import rollback, rollback_to, RollbackError


@click.group("rollback")
def rollback_cmd():
    """Rollback applied environment profiles."""


@rollback_cmd.command("undo")
@click.argument("project")
@click.option("--steps", default=1, show_default=True, help="Number of steps to roll back.")
@click.option("--password", default=None, help="Password for encrypted profiles.")
def undo_cmd(project, steps, password):
    """Roll back the last N applied profiles for PROJECT."""
    try:
        entries = rollback(project, steps=steps, password=password)
        for entry in entries:
            click.echo(f"Rolled back to: {entry['profile']} (was applied at {entry['applied_at']})")
    except RollbackError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@rollback_cmd.command("to")
@click.argument("project")
@click.argument("profile")
@click.option("--password", default=None, help="Password for encrypted profiles.")
def to_cmd(project, profile, password):
    """Roll back PROJECT to a specific PROFILE by name."""
    try:
        entry = rollback_to(project, profile, password=password)
        click.echo(f"Rolled back to: {entry['profile']} (applied at {entry['applied_at']})")
    except RollbackError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

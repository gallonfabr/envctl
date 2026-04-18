"""CLI commands for profile locking."""

import click
from envctl.lock import lock_profile, unlock_profile, is_locked, LockError


@click.group("lock")
def lock_cmd():
    """Lock or unlock profiles to prevent modifications."""


@lock_cmd.command("set")
@click.argument("project")
@click.argument("profile")
def set_lock_cmd(project, profile):
    """Lock a profile."""
    try:
        lock_profile(project, profile)
        click.echo(f"Profile '{project}/{profile}' locked.")
    except LockError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@lock_cmd.command("unset")
@click.argument("project")
@click.argument("profile")
def unset_lock_cmd(project, profile):
    """Unlock a profile."""
    try:
        unlock_profile(project, profile)
        click.echo(f"Profile '{project}/{profile}' unlocked.")
    except LockError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@lock_cmd.command("status")
@click.argument("project")
@click.argument("profile")
def status_cmd(project, profile):
    """Show lock status of a profile."""
    locked = is_locked(project, profile)
    state = "locked" if locked else "unlocked"
    click.echo(f"Profile '{project}/{profile}' is {state}.")

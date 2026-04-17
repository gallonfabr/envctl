"""CLI commands for pinning default profiles."""

import click
from envctl.pin import pin_profile, unpin_profile, get_pinned


@click.group("pin")
def pin_cmd():
    """Manage pinned (default) profiles for projects."""


@pin_cmd.command("set")
@click.argument("project")
@click.argument("profile")
def set_pin_cmd(project, profile):
    """Pin PROFILE as the default for PROJECT."""
    try:
        pin_profile(project, profile)
        click.echo(f"Pinned '{profile}' as default for '{project}'.")
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@pin_cmd.command("unset")
@click.argument("project")
def unset_pin_cmd(project):
    """Remove the pinned default for PROJECT."""
    try:
        unpin_profile(project)
        click.echo(f"Unpinned default profile for '{project}'.")
    except (KeyError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@pin_cmd.command("show")
@click.argument("project")
def show_pin_cmd(project):
    """Show the pinned default profile for PROJECT."""
    try:
        pinned = get_pinned(project)
        if pinned:
            click.echo(f"Pinned profile: {pinned}")
        else:
            click.echo("No pinned profile set.")
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

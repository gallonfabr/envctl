"""CLI commands for profile groups."""
import click
from envctl.group import (
    create_group, delete_group, get_group, list_groups,
    add_to_group, remove_from_group, GroupError
)


@click.group("group")
def group_cmd():
    """Manage profile groups."""


@group_cmd.command("create")
@click.argument("group")
@click.argument("members", nargs=-1, required=True, metavar="PROJECT:PROFILE...")
def create_cmd(group, members):
    """Create a group from PROJECT:PROFILE pairs."""
    parsed = []
    for m in members:
        if ":" not in m:
            raise click.BadParameter(f"Expected PROJECT:PROFILE, got '{m}'")
        project, profile = m.split(":", 1)
        parsed.append((project, profile))
    try:
        create_group(group, parsed)
        click.echo(f"Group '{group}' created with {len(parsed)} member(s).")
    except GroupError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@group_cmd.command("delete")
@click.argument("group")
def delete_cmd(group):
    """Delete a group."""
    try:
        delete_group(group)
        click.echo(f"Group '{group}' deleted.")
    except GroupError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@group_cmd.command("list")
def list_cmd():
    """List all groups."""
    groups = list_groups()
    if not groups:
        click.echo("No groups defined.")
    for g in groups:
        click.echo(g)


@group_cmd.command("show")
@click.argument("group")
def show_cmd(group):
    """Show members of a group."""
    try:
        members = get_group(group)
        for m in members:
            click.echo(f"{m['project']}:{m['profile']}")
    except GroupError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@group_cmd.command("add")
@click.argument("group")
@click.argument("member", metavar="PROJECT:PROFILE")
def add_cmd(group, member):
    """Add a member to a group."""
    if ":" not in member:
        raise click.BadParameter(f"Expected PROJECT:PROFILE, got '{member}'")
    project, profile = member.split(":", 1)
    try:
        add_to_group(group, project, profile)
        click.echo(f"Added {project}:{profile} to group '{group}'.")
    except GroupError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@group_cmd.command("remove")
@click.argument("group")
@click.argument("member", metavar="PROJECT:PROFILE")
def remove_cmd(group, member):
    """Remove a member from a group."""
    if ":" not in member:
        raise click.BadParameter(f"Expected PROJECT:PROFILE, got '{member}'")
    project, profile = member.split(":", 1)
    try:
        remove_from_group(group, project, profile)
        click.echo(f"Removed {project}:{profile} from group '{group}'.")
    except GroupError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

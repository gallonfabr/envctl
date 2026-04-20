"""CLI commands for profile access control."""
import click

from envctl.access import (
    AccessError,
    assert_access,
    clear_allowed_users,
    get_allowed_users,
    list_restricted_profiles,
    set_allowed_users,
)


@click.group("access")
def access_cmd():
    """Manage access control for profiles."""


@access_cmd.command("set")
@click.argument("project")
@click.argument("profile")
@click.argument("users", nargs=-1, required=True)
def set_cmd(project: str, profile: str, users: tuple):
    """Set allowed USERS for PROJECT/PROFILE (space-separated)."""
    try:
        set_allowed_users(project, profile, list(users))
        click.echo(
            f"Access restricted to: {', '.join(users)} for '{project}/{profile}'."
        )
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_cmd.command("clear")
@click.argument("project")
@click.argument("profile")
def clear_cmd(project: str, profile: str):
    """Remove access restrictions from PROJECT/PROFILE."""
    try:
        clear_allowed_users(project, profile)
        click.echo(f"Access restrictions cleared for '{project}/{profile}'.")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_cmd.command("show")
@click.argument("project")
@click.argument("profile")
def show_cmd(project: str, profile: str):
    """Show allowed users for PROJECT/PROFILE."""
    allowed = get_allowed_users(project, profile)
    if allowed is None:
        click.echo(f"'{project}/{profile}' is unrestricted (no access list).")
    else:
        click.echo(f"Allowed users: {', '.join(allowed) if allowed else '(none)'}")


@access_cmd.command("list")
@click.argument("project")
def list_cmd(project: str):
    """List profiles in PROJECT that have access restrictions."""
    restricted = list_restricted_profiles(project)
    if not restricted:
        click.echo(f"No restricted profiles in project '{project}'.")
    else:
        for name in restricted:
            click.echo(name)


@access_cmd.command("check")
@click.argument("project")
@click.argument("profile")
@click.option("--user", default=None, help="User to check (default: current OS user).")
def check_cmd(project: str, profile: str, user: str):
    """Check whether USER can access PROJECT/PROFILE."""
    try:
        assert_access(project, profile, user)
        click.echo("Access granted.")
    except AccessError as exc:
        click.echo(f"Access denied: {exc}", err=True)
        raise SystemExit(1)

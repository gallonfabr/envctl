"""CLI commands for profile status badges."""
import click

from envctl.badge import BadgeError, format_badge, profile_badge, project_badges


@click.group(name="badge")
def badge_cmd():
    """Show status badges for profiles."""


@badge_cmd.command(name="show")
@click.argument("project")
@click.argument("profile")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON-like dict")
def show_cmd(project: str, profile: str, as_json: bool):
    """Show badge for a single PROJECT/PROFILE."""
    try:
        badge = profile_badge(project, profile)
    except BadgeError as exc:
        raise click.ClickException(str(exc))

    if as_json:
        for key, value in badge.items():
            click.echo(f"{key}: {value}")
    else:
        click.echo(format_badge(badge))


@badge_cmd.command(name="project")
@click.argument("project")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON-like dicts")
def project_cmd(project: str, as_json: bool):
    """Show badges for all profiles in PROJECT."""
    try:
        badges = project_badges(project)
    except BadgeError as exc:
        raise click.ClickException(str(exc))

    if not badges:
        click.echo(f"No profiles found in project '{project}'.")
        return

    for badge in badges:
        if as_json:
            click.echo(str(badge))
        else:
            click.echo(format_badge(badge))

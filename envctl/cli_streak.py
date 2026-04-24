"""CLI commands for profile apply streaks."""
import click

from envctl.streak import get_streak, record_apply, reset_streak, StreakError


@click.group("streak")
def streak_cmd():
    """View and manage profile apply streaks."""


@streak_cmd.command("show")
@click.argument("project")
@click.argument("profile")
def show_cmd(project: str, profile: str):
    """Show current streak info for a profile."""
    info = get_streak(project, profile)
    if info.last_applied is None:
        click.echo(f"No streak data for {project}/{profile}.")
        return
    click.echo(f"Profile : {project}/{profile}")
    click.echo(f"Current streak : {info.current} day(s)")
    click.echo(f"Longest streak : {info.longest} day(s)")
    click.echo(f"Last applied   : {info.last_applied}")


@streak_cmd.command("record")
@click.argument("project")
@click.argument("profile")
def record_cmd(project: str, profile: str):
    """Manually record an apply for streak tracking."""
    try:
        info = record_apply(project, profile)
        click.echo(
            f"Streak updated: {info.current} day(s) current, "
            f"{info.longest} day(s) longest."
        )
    except StreakError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@streak_cmd.command("reset")
@click.argument("project")
@click.argument("profile")
def reset_cmd(project: str, profile: str):
    """Reset streak data for a profile."""
    try:
        reset_streak(project, profile)
        click.echo(f"Streak reset for {project}/{profile}.")
    except StreakError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

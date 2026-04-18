"""CLI commands for profile scheduling."""
import click
from envctl.schedule import set_schedule, remove_schedule, list_schedules, active_now, ScheduleError


@click.group("schedule")
def schedule_cmd():
    """Manage scheduled profile activation."""


@schedule_cmd.command("set")
@click.argument("project")
@click.argument("profile")
@click.option("--start", required=True, help="Start time HH:MM")
@click.option("--end", required=True, help="End time HH:MM")
@click.option("--days", required=True, help="Comma-separated days e.g. mon,tue,wed")
def set_cmd(project, profile, start, end, days):
    """Set a schedule for a profile."""
    day_list = [d.strip() for d in days.split(",")]
    try:
        entry = set_schedule(project, profile, start, end, day_list)
        click.echo(f"Schedule set: {entry}")
    except ScheduleError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@schedule_cmd.command("remove")
@click.argument("project")
@click.argument("profile")
def remove_cmd(project, profile):
    """Remove a schedule."""
    try:
        remove_schedule(project, profile)
        click.echo(f"Schedule removed for {project}/{profile}")
    except ScheduleError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@schedule_cmd.command("list")
@click.option("--project", default=None)
def list_cmd(project):
    """List schedules."""
    entries = list_schedules(project)
    if not entries:
        click.echo("No schedules found.")
        return
    for e in entries:
        click.echo(f"{e['project']}/{e['profile']} {e['start']}-{e['end']} {','.join(e['days'])}")


@schedule_cmd.command("check")
@click.argument("project")
@click.argument("profile")
def check_cmd(project, profile):
    """Check if a profile schedule is currently active."""
    if active_now(project, profile):
        click.echo(f"{project}/{profile} is ACTIVE now.")
    else:
        click.echo(f"{project}/{profile} is NOT active now.")

"""CLI commands for managing profile triggers."""
import click

from envctl.trigger import (
    TriggerError,
    VALID_EVENTS,
    fire_trigger,
    get_triggers,
    remove_trigger,
    set_trigger,
)


@click.group("trigger")
def trigger_cmd() -> None:
    """Manage shell triggers for profile lifecycle events."""


@trigger_cmd.command("set")
@click.argument("project")
@click.argument("profile")
@click.argument("event")
@click.argument("command")
def set_cmd(project: str, profile: str, event: str, command: str) -> None:
    """Attach COMMAND to EVENT for PROJECT/PROFILE."""
    try:
        set_trigger(project, profile, event, command)
        click.echo(f"Trigger set: [{event}] -> {command!r} on {project}/{profile}")
    except TriggerError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@trigger_cmd.command("remove")
@click.argument("project")
@click.argument("profile")
@click.argument("event")
def remove_cmd(project: str, profile: str, event: str) -> None:
    """Remove the trigger for EVENT from PROJECT/PROFILE."""
    try:
        remove_trigger(project, profile, event)
        click.echo(f"Trigger for '{event}' removed from {project}/{profile}.")
    except TriggerError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@trigger_cmd.command("list")
@click.argument("project")
@click.argument("profile")
def list_cmd(project: str, profile: str) -> None:
    """List all triggers for PROJECT/PROFILE."""
    triggers = get_triggers(project, profile)
    if not triggers:
        click.echo(f"No triggers set for {project}/{profile}.")
        return
    for event, command in sorted(triggers.items()):
        click.echo(f"  {event}: {command}")


@trigger_cmd.command("fire")
@click.argument("project")
@click.argument("profile")
@click.argument("event")
def fire_cmd(project: str, profile: str, event: str) -> None:
    """Manually fire the trigger for EVENT on PROJECT/PROFILE."""
    code = fire_trigger(project, profile, event)
    if code is None:
        click.echo(f"No trigger configured for event '{event}'.")
    elif code == 0:
        click.echo(f"Trigger '{event}' executed successfully.")
    else:
        click.echo(f"Trigger '{event}' exited with code {code}.", err=True)
        raise SystemExit(code)

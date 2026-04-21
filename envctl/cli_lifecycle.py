"""CLI commands for inspecting registered lifecycle hooks."""

import click

from envctl.lifecycle import VALID_EVENTS, list_hooks


@click.group("lifecycle")
def lifecycle_cmd():
    """Manage profile lifecycle hooks."""


@lifecycle_cmd.command("events")
def events_cmd():
    """List all valid lifecycle event names."""
    for event in VALID_EVENTS:
        click.echo(event)


@lifecycle_cmd.command("hooks")
@click.argument("event")
def hooks_cmd(event: str):
    """Show registered hook count for EVENT."""
    if event not in VALID_EVENTS:
        click.echo(
            f"Error: unknown event '{event}'. "
            f"Valid: {', '.join(VALID_EVENTS)}",
            err=True,
        )
        raise SystemExit(1)
    hooks = list_hooks(event)
    if not hooks:
        click.echo(f"No hooks registered for '{event}'.")
    else:
        click.echo(f"{len(hooks)} hook(s) registered for '{event}':")
        for fn in hooks:
            module = getattr(fn, "__module__", "?")
            name = getattr(fn, "__name__", repr(fn))
            click.echo(f"  {module}.{name}")

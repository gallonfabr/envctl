"""CLI commands for label management."""
import click

from envctl.label import (
    LabelError,
    clear_labels,
    find_by_label,
    get_labels,
    remove_label,
    set_label,
)


@click.group("label")
def label_cmd():
    """Manage key=value labels on profiles."""


@label_cmd.command("set")
@click.argument("project")
@click.argument("profile")
@click.argument("key")
@click.argument("value")
def set_cmd(project: str, profile: str, key: str, value: str):
    """Set a label KEY=VALUE on a profile."""
    try:
        set_label(project, profile, key, value)
        click.echo(f"Label '{key}={value}' set on {project}/{profile}.")
    except LabelError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@label_cmd.command("remove")
@click.argument("project")
@click.argument("profile")
@click.argument("key")
def remove_cmd(project: str, profile: str, key: str):
    """Remove a label KEY from a profile."""
    try:
        remove_label(project, profile, key)
        click.echo(f"Label '{key}' removed from {project}/{profile}.")
    except LabelError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@label_cmd.command("list")
@click.argument("project")
@click.argument("profile")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def list_cmd(project: str, profile: str, as_json: bool):
    """List all labels on a profile."""
    try:
        labels = get_labels(project, profile)
    except LabelError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if as_json:
        import json
        click.echo(json.dumps(labels, indent=2))
    elif labels:
        for k, v in sorted(labels.items()):
            click.echo(f"{k}={v}")
    else:
        click.echo("No labels set.")


@label_cmd.command("find")
@click.argument("project")
@click.argument("key")
@click.option("--value", default=None, help="Filter by label value.")
def find_cmd(project: str, key: str, value: str):
    """Find profiles in PROJECT that have label KEY (optionally matching VALUE)."""
    matches = find_by_label(project, key, value)
    if matches:
        for name in matches:
            click.echo(name)
    else:
        click.echo("No matching profiles found.")


@label_cmd.command("clear")
@click.argument("project")
@click.argument("profile")
def clear_cmd(project: str, profile: str):
    """Clear all labels from a profile."""
    try:
        clear_labels(project, profile)
        click.echo(f"All labels cleared from {project}/{profile}.")
    except LabelError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

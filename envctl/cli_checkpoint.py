"""CLI commands for checkpoint management."""
import click

from envctl.checkpoint import (
    CheckpointError,
    create_checkpoint,
    restore_checkpoint,
    list_checkpoints,
    delete_checkpoint,
)


@click.group("checkpoint")
def checkpoint_cmd():
    """Manage named profile checkpoints."""


@checkpoint_cmd.command("create")
@click.argument("project")
@click.argument("profile")
@click.argument("name")
def create_cmd(project: str, profile: str, name: str):
    """Create a checkpoint NAME for PROJECT/PROFILE."""
    try:
        entry = create_checkpoint(project, profile, name)
        click.echo(f"Checkpoint '{name}' created at {entry['created_at']:.0f}.")
    except CheckpointError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@checkpoint_cmd.command("restore")
@click.argument("project")
@click.argument("profile")
@click.argument("name")
def restore_cmd(project: str, profile: str, name: str):
    """Restore PROJECT/PROFILE from checkpoint NAME."""
    try:
        restore_checkpoint(project, profile, name)
        click.echo(f"Profile '{profile}' restored from checkpoint '{name}'.")
    except CheckpointError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@checkpoint_cmd.command("list")
@click.argument("project")
@click.argument("profile")
def list_cmd(project: str, profile: str):
    """List checkpoints for PROJECT/PROFILE."""
    items = list_checkpoints(project, profile)
    if not items:
        click.echo("No checkpoints found.")
        return
    for item in items:
        click.echo(f"  {item['name']}  (saved {item['created_at']:.0f})")


@checkpoint_cmd.command("delete")
@click.argument("project")
@click.argument("profile")
@click.argument("name")
def delete_cmd(project: str, profile: str, name: str):
    """Delete checkpoint NAME from PROJECT/PROFILE."""
    try:
        delete_checkpoint(project, profile, name)
        click.echo(f"Checkpoint '{name}' deleted.")
    except CheckpointError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

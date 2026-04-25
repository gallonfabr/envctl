"""CLI commands for shadow profile management."""

import click

from envctl.shadow import (
    create_shadow,
    promote_shadow,
    discard_shadow,
    has_shadow,
    list_shadows,
    ShadowError,
)


@click.group("shadow")
def shadow_cmd():
    """Manage shadow (experimental) copies of profiles."""


@shadow_cmd.command("create")
@click.argument("project")
@click.argument("profile")
@click.option("--password", "-p", default=None, help="Decryption password for encrypted profiles.")
def create_cmd(project: str, profile: str, password: str):
    """Create a shadow copy of PROFILE in PROJECT."""
    try:
        shadow = create_shadow(project, profile, password=password)
        click.echo(f"Shadow created: {shadow}")
    except ShadowError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@shadow_cmd.command("promote")
@click.argument("project")
@click.argument("profile")
@click.option("--password", "-p", default=None, help="Encryption password.")
def promote_cmd(project: str, profile: str, password: str):
    """Promote the shadow of PROFILE, overwriting the original."""
    try:
        promote_shadow(project, profile, password=password)
        click.echo(f"Shadow promoted to '{profile}'.")
    except ShadowError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@shadow_cmd.command("discard")
@click.argument("project")
@click.argument("profile")
def discard_cmd(project: str, profile: str):
    """Discard the shadow copy of PROFILE without touching the original."""
    try:
        discard_shadow(project, profile)
        click.echo(f"Shadow for '{profile}' discarded.")
    except ShadowError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@shadow_cmd.command("list")
@click.argument("project")
def list_cmd(project: str):
    """List all profiles that have an active shadow in PROJECT."""
    shadows = list_shadows(project)
    if not shadows:
        click.echo("No shadow profiles found.")
    else:
        for name in shadows:
            click.echo(name)

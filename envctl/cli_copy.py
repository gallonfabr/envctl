"""CLI commands for copying and renaming profiles."""

import click
from envctl.copy import copy_profile, rename_profile


@click.group("copy")
def copy_cmd():
    """Copy or rename profiles."""


@copy_cmd.command("profile")
@click.argument("src_project")
@click.argument("src_profile")
@click.argument("dst_project")
@click.argument("dst_profile")
@click.option("--password", "-p", default=None, help="Decryption/encryption password.")
def copy_profile_cmd(src_project, src_profile, dst_project, dst_profile, password):
    """Copy SRC_PROJECT/SRC_PROFILE to DST_PROJECT/DST_PROFILE."""
    try:
        copy_profile(src_project, src_profile, dst_project, dst_profile, password=password)
        click.echo(
            f"Copied '{src_project}/{src_profile}' -> '{dst_project}/{dst_profile}'."
        )
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@copy_cmd.command("rename")
@click.argument("project")
@click.argument("old_name")
@click.argument("new_name")
@click.option("--password", "-p", default=None, help="Decryption/encryption password.")
def rename_profile_cmd(project, old_name, new_name, password):
    """Rename OLD_NAME to NEW_NAME within PROJECT."""
    try:
        rename_profile(project, old_name, new_name, password=password)
        click.echo(f"Renamed '{old_name}' -> '{new_name}' in project '{project}'.")
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

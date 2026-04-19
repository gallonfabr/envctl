"""CLI commands for archiving and restoring project profiles."""

import click
from envctl.archive import export_archive, import_archive, ArchiveError


@click.group("archive")
def archive_cmd():
    """Archive and restore project profile bundles."""


@archive_cmd.command("export")
@click.argument("project")
@click.argument("dest")
def export_cmd(project: str, dest: str):
    """Export all profiles for PROJECT to a zip archive at DEST."""
    try:
        path = export_archive(project, dest)
        click.echo(f"Exported project '{project}' to '{path}'.")
    except ArchiveError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@archive_cmd.command("import")
@click.argument("src")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing project.")
def import_cmd(src: str, overwrite: bool):
    """Import profiles from a zip archive at SRC."""
    try:
        project = import_archive(src, overwrite=overwrite)
        click.echo(f"Imported project '{project}' from '{src}'.")
    except ArchiveError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

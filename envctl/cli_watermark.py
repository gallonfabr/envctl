"""CLI commands for the watermark feature."""

import click

from envctl.watermark import (
    WatermarkError,
    clear_watermark,
    get_watermark,
    set_watermark,
    verify_watermark,
)


@click.group("watermark", help="Attach and verify authorship watermarks on profiles.")
def watermark_cmd() -> None:
    pass


@watermark_cmd.command("set")
@click.argument("project")
@click.argument("profile")
@click.option("--author", required=True, help="Author name or identifier.")
@click.option("--note", default="", help="Optional note.")
def set_cmd(project: str, profile: str, author: str, note: str) -> None:
    """Attach a watermark to a profile."""
    try:
        wm = set_watermark(project, profile, author, note)
        click.echo(f"Watermark set — author: {wm['author']}, checksum: {wm['checksum']}")
    except WatermarkError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@watermark_cmd.command("show")
@click.argument("project")
@click.argument("profile")
def show_cmd(project: str, profile: str) -> None:
    """Show the watermark attached to a profile."""
    try:
        wm = get_watermark(project, profile)
        if wm is None:
            click.echo("No watermark set.")
        else:
            click.echo(f"Author   : {wm['author']}")
            click.echo(f"Note     : {wm.get('note', '')}")
            click.echo(f"Checksum : {wm['checksum']}")
    except WatermarkError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@watermark_cmd.command("verify")
@click.argument("project")
@click.argument("profile")
def verify_cmd(project: str, profile: str) -> None:
    """Verify the integrity of a profile's watermark."""
    try:
        ok = verify_watermark(project, profile)
        if ok:
            click.echo("Watermark OK — checksum verified.")
        else:
            click.echo("Watermark INVALID — checksum mismatch!", err=True)
            raise SystemExit(1)
    except WatermarkError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@watermark_cmd.command("clear")
@click.argument("project")
@click.argument("profile")
def clear_cmd(project: str, profile: str) -> None:
    """Remove the watermark from a profile."""
    try:
        clear_watermark(project, profile)
        click.echo("Watermark cleared.")
    except WatermarkError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

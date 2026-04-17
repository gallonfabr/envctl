"""CLI commands for profile tag management."""

import click
from envctl.tags import add_tag, remove_tag, list_tags, find_by_tag


@click.group("tags")
def tags_cmd():
    """Manage tags on profiles."""


@tags_cmd.command("add")
@click.argument("project")
@click.argument("profile")
@click.argument("tag")
def add_tag_cmd(project, profile, tag):
    """Add TAG to a profile."""
    try:
        add_tag(project, profile, tag)
        click.echo(f"Tag '{tag}' added to {project}/{profile}.")
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@tags_cmd.command("remove")
@click.argument("project")
@click.argument("profile")
@click.argument("tag")
def remove_tag_cmd(project, profile, tag):
    """Remove TAG from a profile."""
    try:
        remove_tag(project, profile, tag)
        click.echo(f"Tag '{tag}' removed from {project}/{profile}.")
    except (KeyError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@tags_cmd.command("list")
@click.argument("project")
@click.argument("profile")
def list_tags_cmd(project, profile):
    """List tags on a profile."""
    try:
        t = list_tags(project, profile)
        if t:
            click.echo("\n".join(t))
        else:
            click.echo("No tags.")
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@tags_cmd.command("find")
@click.argument("tag")
def find_tag_cmd(tag):
    """Find all profiles with TAG."""
    results = find_by_tag(tag)
    if results:
        for project, profile in results:
            click.echo(f"{project}/{profile}")
    else:
        click.echo(f"No profiles found with tag '{tag}'.")

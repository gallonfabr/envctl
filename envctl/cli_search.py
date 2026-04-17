"""CLI commands for searching profiles."""

import click
from envctl.search import search_by_key, search_by_value


@click.group("search")
def search_cmd():
    """Search across environment profiles."""


@search_cmd.command("key")
@click.argument("pattern")
@click.option("--project", "-p", default=None, help="Limit to a specific project.")
@click.option("--password", default=None, help="Password for encrypted profiles.")
def search_key_cmd(pattern, project, password):
    """Search profiles for variables whose KEY matches PATTERN (glob)."""
    results = search_by_key(pattern, project=project, password=password)
    if not results:
        click.echo("No matches found.")
        return
    for r in results:
        click.echo(f"{r['project']}/{r['profile']}  {r['key']}={r['value']}")


@search_cmd.command("value")
@click.argument("pattern")
@click.option("--project", "-p", default=None, help="Limit to a specific project.")
@click.option("--password", default=None, help="Password for encrypted profiles.")
def search_value_cmd(pattern, project, password):
    """Search profiles for variables whose VALUE matches PATTERN (glob)."""
    results = search_by_value(pattern, project=project, password=password)
    if not results:
        click.echo("No matches found.")
        return
    for r in results:
        click.echo(f"{r['project']}/{r['profile']}  {r['key']}={r['value']}")

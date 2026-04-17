"""Main CLI entry point for envctl."""
import click
from envctl.profile import add_profile, get_profile, delete_profile, apply_profile
from envctl.cli_audit import audit_cmd
from envctl.cli_copy import copy_cmd
from envctl.cli_tags import tags_cmd
from envctl.cli_search import search_cmd
from envctl.cli_compare import compare_cmd


@click.group()
def cli():
    """envctl — manage environment variable profiles."""


@cli.command("add")
@click.argument("project")
@click.argument("profile")
@click.argument("vars", nargs=-1)
@click.option("--password", default=None, help="Encrypt profile with password.")
def add_cmd(project, profile, vars, password):
    """Add a new profile with VAR=VALUE pairs."""
    parsed = {}
    for v in vars:
        if "=" not in v:
            raise click.BadParameter(f"Invalid format '{v}', expected KEY=VALUE.")
        k, val = v.split("=", 1)
        parsed[k] = val
    add_profile(project, profile, parsed, password=password)
    click.echo(f"Profile '{profile}' added to project '{project}'.")


@cli.command("get")
@click.argument("project")
@click.argument("profile")
@click.option("--password", default=None)
def get_cmd(project, profile, password):
    """Get and display a profile's variables."""
    try:
        vars = get_profile(project, profile, password=password)
    except KeyError as e:
        raise click.ClickException(str(e))
    for k, v in vars.items():
        click.echo(f"{k}={v}")


@cli.command("apply")
@click.argument("project")
@click.argument("profile")
@click.option("--password", default=None)
def apply_cmd(project, profile, password):
    """Apply a profile to the current shell session."""
    try:
        script = apply_profile(project, profile, password=password)
    except KeyError as e:
        raise click.ClickException(str(e))
    click.echo(script)


@cli.command("delete")
@click.argument("project")
@click.argument("profile")
def delete_cmd(project, profile):
    """Delete a profile."""
    try:
        delete_profile(project, profile)
    except KeyError as e:
        raise click.ClickException(str(e))
    click.echo(f"Profile '{profile}' deleted from project '{project}'.")


@cli.command("list")
@click.argument("project")
def list_cmd(project):
    """List profiles for a project."""
    from envctl.storage import list_profiles
    profiles = list_profiles(project)
    if not profiles:
        click.echo("No profiles found.")
    for p in profiles:
        click.echo(p)


cli.add_command(audit_cmd)
cli.add_command(copy_cmd)
cli.add_command(tags_cmd)
cli.add_command(search_cmd)
cli.add_command(compare_cmd)

"""CLI commands for profile inheritance."""
import click

from envctl.inherit import inherit_profile, InheritError


@click.group("inherit")
def inherit_cmd():
    """Inherit vars from a parent profile."""


@inherit_cmd.command("apply")
@click.argument("project")
@click.argument("profile")
@click.argument("parent_project")
@click.argument("parent_profile")
@click.option("--password", default=None, help="Password for child profile.")
@click.option("--parent-password", default=None, help="Password for parent profile.")
def apply_cmd(
    project,
    profile,
    parent_project,
    parent_profile,
    password,
    parent_password,
):
    """Merge PARENT_PROJECT/PARENT_PROFILE vars into PROJECT/PROFILE as defaults."""
    try:
        merged = inherit_profile(
            project,
            profile,
            parent_project,
            parent_profile,
            password=password,
            parent_password=parent_password,
        )
        click.echo(
            f"Inherited {len(merged)} var(s) into '{project}/{profile}' "
            f"from '{parent_project}/{parent_profile}'."
        )
    except InheritError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

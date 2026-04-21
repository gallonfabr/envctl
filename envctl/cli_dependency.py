"""CLI commands for managing profile dependencies."""

import click

from envctl.dependency import (
    DependencyError,
    add_dependency,
    get_dependencies,
    remove_dependency,
    resolve_order,
)


@click.group("dependency", help="Manage profile dependencies.")
def dependency_cmd() -> None:  # pragma: no cover
    pass


@dependency_cmd.command("add")
@click.argument("project")
@click.argument("profile")
@click.argument("dep_project")
@click.argument("dep_profile")
def add_cmd(project: str, profile: str, dep_project: str, dep_profile: str) -> None:
    """Add DEP_PROJECT/DEP_PROFILE as a dependency of PROJECT/PROFILE."""
    try:
        add_dependency(project, profile, dep_project, dep_profile)
        click.echo(f"Added dependency '{dep_project}/{dep_profile}' to '{project}/{profile}'.")
    except DependencyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@dependency_cmd.command("remove")
@click.argument("project")
@click.argument("profile")
@click.argument("dep_project")
@click.argument("dep_profile")
def remove_cmd(project: str, profile: str, dep_project: str, dep_profile: str) -> None:
    """Remove DEP_PROJECT/DEP_PROFILE from dependencies of PROJECT/PROFILE."""
    try:
        remove_dependency(project, profile, dep_project, dep_profile)
        click.echo(f"Removed dependency '{dep_project}/{dep_profile}' from '{project}/{profile}'.")
    except DependencyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@dependency_cmd.command("list")
@click.argument("project")
@click.argument("profile")
def list_cmd(project: str, profile: str) -> None:
    """List direct dependencies of PROJECT/PROFILE."""
    try:
        deps = get_dependencies(project, profile)
        if not deps:
            click.echo("No dependencies.")
        else:
            for dep in deps:
                click.echo(f"  {dep['project']}/{dep['profile']}")
    except DependencyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@dependency_cmd.command("resolve")
@click.argument("project")
@click.argument("profile")
def resolve_cmd(project: str, profile: str) -> None:
    """Show full resolved dependency order for PROJECT/PROFILE."""
    try:
        order = resolve_order(project, profile)
        if not order:
            click.echo("No dependencies to resolve.")
        else:
            click.echo("Resolved order (dependencies first):")
            for dep in order:
                click.echo(f"  {dep['project']}/{dep['profile']}")
    except DependencyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

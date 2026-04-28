"""cli_quota_ceiling.py — CLI commands for quota-ceiling combined checks."""
import click

from envctl.quota_ceiling import (
    check_var_ceiling,
    check_project_quota,
    QuotaCeilingError,
)


@click.group("quota-ceiling")
def quota_ceiling_cmd() -> None:
    """Inspect combined quota and ceiling constraints."""


@quota_ceiling_cmd.command("check-vars")
@click.argument("project")
@click.argument("profile")
@click.option(
    "--incoming",
    default=1,
    show_default=True,
    help="Number of vars you intend to add.",
)
def check_vars_cmd(project: str, profile: str, incoming: int) -> None:
    """Check whether adding INCOMING vars to PROFILE is within ceiling."""
    if incoming < 1:
        click.echo("error: --incoming must be a positive integer", err=True)
        raise SystemExit(1)

    try:
        result = check_var_ceiling(project, profile, incoming)
    except QuotaCeilingError as exc:
        click.echo(f"error: {exc}", err=True)
        raise SystemExit(1)

    if result.allowed:
        click.echo(f"ok: {incoming} var(s) can be added to '{profile}'")
    else:
        click.echo(f"denied: {result.reason}")
        raise SystemExit(1)


@quota_ceiling_cmd.command("check-quota")
@click.argument("project")
def check_quota_cmd(project: str) -> None:
    """Check whether adding a new profile to PROJECT is within quota."""
    try:
        result = check_project_quota(project)
    except QuotaCeilingError as exc:
        click.echo(f"error: {exc}", err=True)
        raise SystemExit(1)

    if result.allowed:
        click.echo(f"ok: project '{project}' is within quota")
    else:
        click.echo(f"denied: {result.reason}")
        raise SystemExit(1)

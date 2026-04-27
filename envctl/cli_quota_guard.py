"""cli_quota_guard.py — CLI sub-commands for quota-guard status inspection."""
from __future__ import annotations

import click

from envctl.quota_guard import quota_status, QuotaGuardError
from envctl.quota import set_quota, remove_quota, QuotaError


@click.group("quota-guard")
def quota_guard_cmd() -> None:
    """Inspect and manage profile-count quotas for projects."""


@quota_guard_cmd.command("status")
@click.argument("project")
def status_cmd(project: str) -> None:
    """Show quota usage for PROJECT."""
    info = quota_status(project)
    quota_display = str(info["quota"]) if info["quota"] is not None else "unlimited"
    available_display = str(info["available"]) if info["available"] is not None else "unlimited"
    exceeded_marker = "  *** EXCEEDED ***" if info["exceeded"] else ""
    click.echo(f"Project  : {info['project']}")
    click.echo(f"Quota    : {quota_display}")
    click.echo(f"Used     : {info['used']}")
    click.echo(f"Available: {available_display}{exceeded_marker}")


@quota_guard_cmd.command("set")
@click.argument("project")
@click.argument("limit", type=int)
def set_cmd(project: str, limit: int) -> None:
    """Set the profile-count quota for PROJECT to LIMIT."""
    try:
        set_quota(project, limit)
        click.echo(f"Quota for '{project}' set to {limit}.")
    except QuotaError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@quota_guard_cmd.command("remove")
@click.argument("project")
def remove_cmd(project: str) -> None:
    """Remove the profile-count quota for PROJECT."""
    try:
        remove_quota(project)
        click.echo(f"Quota for '{project}' removed.")
    except QuotaError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

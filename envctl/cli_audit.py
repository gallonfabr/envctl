"""CLI commands for audit log inspection."""

import click
from envctl.audit import read_events, clear_audit_log


@click.group("audit")
def audit_cmd():
    """View and manage the audit log."""
    pass


@audit_cmd.command("log")
@click.option("--project", "-p", default=None, help="Filter by project name.")
@click.option("--limit", "-n", default=50, show_default=True, help="Max number of entries.")
def log_cmd(project, limit):
    """Display recent audit log entries."""
    events = read_events(project=project, limit=limit)
    if not events:
        click.echo("No audit log entries found.")
        return
    for e in events:
        project_str = e.get("project", "-")
        profile_str = e.get("profile", "-")
        action_str = e.get("action", "-").upper().ljust(8)
        ts = e.get("timestamp", "-")
        extras = {k: v for k, v in e.items() if k not in ("timestamp", "action", "project", "profile")}
        extra_str = " " + str(extras) if extras else ""
        click.echo(f"[{ts}] {action_str} {project_str}/{profile_str}{extra_str}")


@audit_cmd.command("clear")
@click.confirmation_option(prompt="Are you sure you want to clear the audit log?")
def clear_cmd():
    """Clear all audit log entries."""
    clear_audit_log()
    click.echo("Audit log cleared.")

"""CLI commands for environment drift detection."""

import os
import click
from envctl.watch import check_drift, drift_summary


@click.group("watch")
def watch_cmd():
    """Drift detection between profiles and current environment."""


@watch_cmd.command("check")
@click.argument("project")
@click.argument("profile")
@click.option("--password", default=None, help="Decryption password if profile is encrypted.")
@click.option("--summary", "show_summary", is_flag=True, default=False, help="Show summary only.")
def check_cmd(project, profile, password, show_summary):
    """Check for drift between current env and a stored profile."""
    current_env = dict(os.environ)

    try:
        drifts = check_drift(project, profile, current_env, password=password)
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    if not drifts:
        click.echo("No drift detected. Environment matches profile.")
        return

    if show_summary:
        summary = drift_summary(drifts)
        for status, count in summary.items():
            click.echo(f"{status}: {count}")
        return

    for entry in drifts:
        key = entry["key"]
        status = entry["status"]
        if status == "missing":
            click.echo(f"  MISSING  {key} (expected: {entry['expected']!r})")
        elif status == "changed":
            click.echo(f"  CHANGED  {key}: {entry['actual']!r} -> {entry['expected']!r}")

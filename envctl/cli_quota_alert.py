"""CLI commands for quota alert checks."""
import click

from envctl.quota_alert import check_alert, check_all_alerts, QuotaAlertError


@click.group("quota-alert", help="Check quota usage alerts.")
def quota_alert_cmd() -> None:
    pass


@quota_alert_cmd.command("check")
@click.argument("project")
@click.option(
    "--threshold",
    default=0.8,
    show_default=True,
    type=float,
    help="Alert threshold as a fraction (0.0–1.0).",
)
def check_cmd(project: str, threshold: float) -> None:
    """Check quota alert status for PROJECT."""
    try:
        status = check_alert(project, threshold=threshold)
    except QuotaAlertError as exc:
        raise click.ClickException(str(exc))

    if status is None:
        click.echo(f"No quota configured for project '{project}'.")
        return

    click.echo(status.message)
    if status.triggered:
        raise SystemExit(1)


@quota_alert_cmd.command("check-all")
@click.option(
    "--threshold",
    default=0.8,
    show_default=True,
    type=float,
    help="Alert threshold as a fraction (0.0–1.0).",
)
def check_all_cmd(threshold: float) -> None:
    """Check quota alerts for all projects."""
    try:
        statuses = check_all_alerts(threshold=threshold)
    except QuotaAlertError as exc:
        raise click.ClickException(str(exc))

    if not statuses:
        click.echo("No quota-configured projects found.")
        return

    any_triggered = False
    for s in statuses:
        click.echo(s.message)
        if s.triggered:
            any_triggered = True

    if any_triggered:
        raise SystemExit(1)

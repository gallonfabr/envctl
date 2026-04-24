"""CLI commands for profile health checks."""
import json
import click
from envctl.health import check_profile, HealthError


@click.group("health")
def health_cmd():
    """Profile health scoring commands."""


@health_cmd.command("check")
@click.argument("project")
@click.argument("profile")
@click.option("--password", "-p", default=None, help="Decryption password.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def check_cmd(project: str, profile: str, password: str, as_json: bool):
    """Check the health of a profile and display a score."""
    try:
        report = check_profile(project, profile, password=password)
    except HealthError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if as_json:
        data = {
            "project": report.project,
            "profile": report.profile,
            "score": report.score,
            "grade": report.grade,
            "healthy": report.healthy,
            "issues": [
                {"severity": i.severity, "code": i.code, "message": i.message}
                for i in report.issues
            ],
        }
        click.echo(json.dumps(data, indent=2))
        return

    status = "✓ Healthy" if report.healthy else "✗ Unhealthy"
    click.echo(f"[{report.grade}] {report.project}/{report.profile} — {report.score}/100  {status}")
    if report.issues:
        click.echo("Issues:")
        for issue in report.issues:
            icon = "!" if issue.severity == "error" else "~"
            click.echo(f"  [{icon}] {issue.code}: {issue.message}")
    else:
        click.echo("  No issues found.")

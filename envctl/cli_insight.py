"""CLI commands for profile/project insights."""
import json as _json

import click

from envctl.insight import InsightError, profile_insight, project_insight


@click.group("insight")
def insight_cmd():
    """Surface health and usage insights for profiles."""


@insight_cmd.command("profile")
@click.argument("project")
@click.argument("profile")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def profile_cmd(project: str, profile: str, as_json: bool):
    """Show insight for a single profile."""
    try:
        ins = profile_insight(project, profile)
    except InsightError as exc:
        raise click.ClickException(str(exc))

    if as_json:
        click.echo(_json.dumps(ins.__dict__, default=str))
        return

    click.echo(f"Profile : {ins.project}/{ins.profile}")
    click.echo(f"Vars    : {ins.var_count}")
    click.echo(f"Locked  : {ins.is_locked}")
    click.echo(f"Expired : {ins.is_expired}")
    click.echo(f"Pinned  : {ins.is_pinned}")
    click.echo(f"Expiry  : {ins.expiry or 'none'}")
    click.echo(f"Applies : {ins.recent_applies} (last 30 events)")
    click.echo(f"Tags    : {', '.join(ins.tags) or 'none'}")


@insight_cmd.command("project")
@click.argument("project")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def project_cmd(project: str, as_json: bool):
    """Show aggregated insight for a project."""
    try:
        ins = project_insight(project)
    except InsightError as exc:
        raise click.ClickException(str(exc))

    if as_json:
        data = {
            "project": ins.project,
            "profile_count": ins.profile_count,
            "total_vars": ins.total_vars,
            "locked_count": ins.locked_count,
            "expired_count": ins.expired_count,
            "pinned_profile": ins.pinned_profile,
            "profiles": [p.__dict__ for p in ins.profiles],
        }
        click.echo(_json.dumps(data, default=str))
        return

    click.echo(f"Project        : {ins.project}")
    click.echo(f"Profiles       : {ins.profile_count}")
    click.echo(f"Total vars     : {ins.total_vars}")
    click.echo(f"Locked         : {ins.locked_count}")
    click.echo(f"Expired        : {ins.expired_count}")
    click.echo(f"Pinned profile : {ins.pinned_profile or 'none'}")
    if ins.profiles:
        click.echo("\nPer-profile summary:")
        for p in ins.profiles:
            flags = []
            if p.is_locked:
                flags.append("locked")
            if p.is_expired:
                flags.append("expired")
            if p.is_pinned:
                flags.append("pinned")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            click.echo(f"  {p.profile}: {p.var_count} vars, {p.recent_applies} applies{flag_str}")

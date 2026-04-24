"""CLI commands for profile quality rating."""

from __future__ import annotations

import click

from envctl.rating import rate_profile, RatingError
from envctl.storage import list_projects, list_profiles


@click.group("rating")
def rating_cmd() -> None:
    """Profile quality rating commands."""


@rating_cmd.command("show")
@click.argument("project")
@click.argument("profile")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show_cmd(project: str, profile: str, as_json: bool) -> None:
    """Show quality rating for a profile."""
    try:
        rating = rate_profile(project, profile)
    except RatingError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        import json
        click.echo(json.dumps({
            "project": rating.project,
            "profile": rating.profile,
            "score": rating.score,
            "max_score": rating.max_score,
            "grade": rating.grade,
            "breakdown": rating.breakdown,
        }, indent=2))
    else:
        click.echo(f"Profile : {rating.project}/{rating.profile}")
        click.echo(f"Grade   : {rating.grade}  ({rating.score}/{rating.max_score})")
        click.echo("Breakdown:")
        for key, pts in rating.breakdown.items():
            click.echo(f"  {key:<16} {pts:>3} pts")


@rating_cmd.command("project")
@click.argument("project")
def project_cmd(project: str) -> None:
    """Show ratings for all profiles in a project."""
    profiles = list_profiles(project)
    if not profiles:
        click.echo(f"No profiles found for project '{project}'.")
        return

    rows = []
    for profile in profiles:
        try:
            r = rate_profile(project, profile)
            rows.append((profile, r.grade, r.score, r.max_score))
        except RatingError:
            rows.append((profile, "?", 0, 0))

    click.echo(f"{'Profile':<24} {'Grade':<6} {'Score'}")
    click.echo("-" * 40)
    for name, grade, score, max_score in rows:
        click.echo(f"{name:<24} {grade:<6} {score}/{max_score}")

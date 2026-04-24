"""CLI commands for impact analysis."""
import click

from envctl.impact import analyze_key_impact, analyze_value_impact, format_impact_report, ImpactError


@click.group("impact")
def impact_cmd():
    """Analyse which profiles are affected by a key or value."""


@impact_cmd.command("key")
@click.argument("key")
@click.option("--password", "-p", default=None, help="Password for encrypted profiles.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def key_cmd(key: str, password: str | None, as_json: bool):
    """Show all profiles that define KEY."""
    try:
        result = analyze_key_impact(key, password=password)
    except ImpactError as exc:
        raise click.ClickException(str(exc))

    if as_json:
        import json
        click.echo(json.dumps({"key": result.key, "affected": result.affected}, indent=2))
    else:
        click.echo(format_impact_report(result))


@impact_cmd.command("value")
@click.argument("value")
@click.option("--password", "-p", default=None, help="Password for encrypted profiles.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def value_cmd(value: str, password: str | None, as_json: bool):
    """Show all profiles whose vars contain VALUE."""
    try:
        hits = analyze_value_impact(value, password=password)
    except ImpactError as exc:
        raise click.ClickException(str(exc))

    if as_json:
        import json
        click.echo(json.dumps(hits, indent=2))
    else:
        if not hits:
            click.echo(f"No profiles contain value {value!r}")
            return
        click.echo(f"Profiles containing value {value!r}:")
        for entry in hits:
            keys_str = ", ".join(entry["keys"])
            click.echo(f"  - {entry['project']} / {entry['profile']}  (keys: {keys_str})")

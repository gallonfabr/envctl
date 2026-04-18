"""CLI commands for merging profiles."""

import click
from envctl.merge import merge_profiles, STRATEGY_OURS, STRATEGY_THEIRS, STRATEGY_ERROR


@click.group("merge")
def merge_cmd():
    """Merge environment profiles."""


@merge_cmd.command("run")
@click.argument("project")
@click.argument("base")
@click.argument("other")
@click.argument("dest")
@click.option(
    "--strategy",
    type=click.Choice([STRATEGY_OURS, STRATEGY_THEIRS, STRATEGY_ERROR]),
    default=STRATEGY_ERROR,
    show_default=True,
    help="Conflict resolution strategy.",
)
@click.option("--password", default=None, help="Encrypt destination profile.")
def run_cmd(project, base, other, dest, strategy, password):
    """Merge BASE and OTHER profiles into DEST for PROJECT."""
    try:
        merged = merge_profiles(
            project, base, other, dest, strategy=strategy, password=password
        )
        click.echo(f"Merged {len(merged)} variable(s) into '{dest}'.")
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

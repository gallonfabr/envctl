"""CLI commands for comparing profiles."""
import click
from envctl.compare import compare_profiles, compare_summary
from envctl.diff import format_diff


@click.group("compare")
def compare_cmd():
    """Compare environment profiles."""


@compare_cmd.command("run")
@click.argument("project_a")
@click.argument("profile_a")
@click.argument("project_b")
@click.argument("profile_b")
@click.option("--password-a", default=None, help="Password for profile A.")
@click.option("--password-b", default=None, help="Password for profile B.")
@click.option("--summary", is_flag=True, default=False, help="Show summary only.")
def run_cmd(project_a, profile_a, project_b, profile_b, password_a, password_b, summary):
    """Compare two profiles and show differences."""
    try:
        diff = compare_profiles(
            project_a, profile_a, project_b, profile_b, password_a, password_b
        )
    except KeyError as e:
        raise click.ClickException(str(e))

    if summary:
        click.echo(compare_summary(diff))
    else:
        output = format_diff(diff)
        if output:
            click.echo(output)
        else:
            click.echo("Profiles are identical.")

"""CLI commands for template rendering."""
import click
from envctl.template import render_profile_template, list_template_vars


@click.group(name="template")
def template_cmd():
    """Render templates using profile variables."""


@template_cmd.command(name="render")
@click.argument("project")
@click.argument("profile")
@click.argument("template_str")
@click.option("--password", "-p", default=None, help="Decryption password")
def render_cmd(project: str, profile: str, template_str: str, password):
    """Render a template string using variables from a profile.

    Example: envctl template render myproject prod '{{HOST}}:{{PORT}}'
    """
    try:
        result = render_profile_template(template_str, project, profile, password=password)
        click.echo(result)
    except KeyError as e:
        click.echo(f"Error: missing variable {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@template_cmd.command(name="vars")
@click.argument("template_str")
def vars_cmd(template_str: str):
    """List all variable placeholders in a template string."""
    found = list_template_vars(template_str)
    if not found:
        click.echo("No variables found.")
    else:
        for var in found:
            click.echo(var)

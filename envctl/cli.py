import click
from envctl.profile import add_profile, get_profile, delete_profile, apply_profile
from envctl.storage import list_projects, list_profiles


@click.group()
def cli():
    """envctl — manage and switch between environment variable profiles."""
    pass


@cli.command("add")
@click.argument("project")
@click.argument("profile")
@click.option("--var", "-v", multiple=True, help="VAR=VALUE pairs")
@click.option("--encrypt", "-e", is_flag=True, help="Encrypt the profile")
@click.password_option("--password", "-p", required=False, default=None, help="Encryption password")
def add_cmd(project, profile, var, encrypt, password):
    """Add a new profile for a project."""
    variables = {}
    for v in var:
        if "=" not in v:
            raise click.BadParameter(f"Invalid format '{v}', expected VAR=VALUE")
        key, value = v.split("=", 1)
        variables[key] = value
    if encrypt and not password:
        password = click.prompt("Password", hide_input=True)
    add_profile(project, profile, variables, password=password if encrypt else None)
    click.echo(f"Profile '{profile}' added for project '{project}'.")


@cli.command("get")
@click.argument("project")
@click.argument("profile")
@click.option("--password", "-p", default=None, help="Decryption password")
def get_cmd(project, profile, password):
    """Display variables in a profile."""
    data = get_profile(project, profile, password=password)
    if data is None:
        click.echo("Profile not found.", err=True)
        return
    for k, v in data.items():
        click.echo(f"{k}={v}")


@cli.command("apply")
@click.argument("project")
@click.argument("profile")
@click.option("--password", "-p", default=None, help="Decryption password")
def apply_cmd(project, profile, password):
    """Print export statements to apply a profile."""
    exports = apply_profile(project, profile, password=password)
    if exports is None:
        click.echo("Profile not found.", err=True)
        return
    for line in exports:
        click.echo(line)


@cli.command("delete")
@click.argument("("profile")
@click.confirmation_option(prompt="Are you sure you want to delete this profile?")
def delete_cmd(project, profile):
    """Delete a profile."""
    deleted = delete_profile(project, profile)
    if deleted:
        click.echo(f"Profile '{profile}' deleted from project '{project}'.")
    else:
        click.echo("Profile not found.", err=True)


@cli.command("list")
@click.argument("project", required=False)
def list_cmd(project):
    """List projects or profiles within a project."""
    if project:
        profiles = list_profiles(project)
        if not profiles:
            click.echo(f"No profiles found for project '{project}'.")
        for p in profiles:
            click.echo(p)
    else:
        projects = list_projects()
        if not projects:
            click.echo("No projects found.")
        for proj in projects:
            click.echo(proj)


if __name__ == "__main__":
    cli()

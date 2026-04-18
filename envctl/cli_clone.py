"""CLI commands for cloning profiles across projects."""
import click
from envctl.clone import clone_profile, mirror_project
from envctl.storage import list_profiles


@click.group("clone")
def clone_cmd():
    """Clone profiles across projects."""


@clone_cmd.command("profile")
@click.argument("src_project")
@click.argument("src_profile")
@click.argument("dst_project")
@click.argument("dst_profile")
@click.option("--password", "-p", default=None, help="Password for encrypted profiles.")
def clone_profile_cmd(src_project, src_profile, dst_project, dst_profile, password):
    """Clone SRC_PROFILE from SRC_PROJECT into DST_PROJECT as DST_PROFILE."""
    try:
        clone_profile(src_project, src_profile, dst_project, dst_profile, password=password)
        click.echo(f"Cloned '{src_project}/{src_profile}' -> '{dst_project}/{dst_profile}'.")
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@clone_cmd.command("mirror")
@click.argument("src_project")
@click.argument("dst_project")
@click.option("--password", "-p", default=None, help="Password for encrypted profiles.")
def mirror_cmd(src_project, dst_project, password):
    """Mirror all profiles from SRC_PROJECT into DST_PROJECT."""
    try:
        profiles = list_profiles(src_project)
        if not profiles:
            click.echo(f"No profiles found in '{src_project}'.")
            return
        cloned = mirror_project(src_project, dst_project, profiles, password=password)
        for name in cloned:
            click.echo(f"  Cloned: {name}")
        click.echo(f"Mirrored {len(cloned)} profile(s) to '{dst_project}'.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

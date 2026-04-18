"""CLI commands for promoting profiles between projects."""

import click
from envctl.promote import promote_profile, PromoteError


@click.group("promote")
def promote_cmd():
    """Promote profiles across projects."""


@promote_cmd.command("run")
@click.argument("src_project")
@click.argument("src_profile")
@click.argument("dst_project")
@click.option("--dst-profile", default=None, help="Destination profile name (default: same as source).")
@click.option("--password", default=None, help="Password for encrypted profiles.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite destination if it exists.")
def run_cmd(src_project, src_profile, dst_project, dst_profile, password, overwrite):
    """Promote SRC_PROJECT/SRC_PROFILE to DST_PROJECT."""
    try:
        vars_ = promote_profile(
            src_project,
            src_profile,
            dst_project,
            dst_profile=dst_profile,
            password=password,
            overwrite=overwrite,
        )
        effective_dst = dst_profile or src_profile
        click.echo(
            f"Promoted '{src_project}/{src_profile}' -> '{dst_project}/{effective_dst}' "
            f"({len(vars_)} vars)."
        )
    except PromoteError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

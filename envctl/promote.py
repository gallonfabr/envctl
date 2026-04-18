"""Promote a profile from one project to another (e.g. staging -> production)."""

from envctl.profile import get_profile, add_profile
from envctl.audit import log_event


class PromoteError(Exception):
    pass


def promote_profile(
    src_project: str,
    src_profile: str,
    dst_project: str,
    dst_profile: str | None = None,
    password: str | None = None,
    overwrite: bool = False,
) -> dict:
    """Copy a profile across projects, optionally renaming it.

    Returns the vars dict that was promoted.
    """
    dst_profile = dst_profile or src_profile

    src = get_profile(src_project, src_profile, password=password)
    if src is None:
        raise PromoteError(f"Source profile '{src_project}/{src_profile}' not found.")

    existing = get_profile(dst_project, dst_profile)
    if existing is not None and not overwrite:
        raise PromoteError(
            f"Destination profile '{dst_project}/{dst_profile}' already exists. "
            "Use overwrite=True to replace it."
        )

    add_profile(dst_project, dst_profile, src, password=password)

    log_event(
        "promote",
        src_project,
        src_profile,
        details={
            "dst_project": dst_project,
            "dst_profile": dst_profile,
            "overwrite": overwrite,
        },
    )

    return src

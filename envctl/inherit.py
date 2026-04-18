"""Profile inheritance — merge a parent profile's vars as defaults."""
from __future__ import annotations

from typing import Optional

from envctl.profile import get_profile, add_profile
from envctl.audit import log_event


class InheritError(Exception):
    pass


def inherit_profile(
    project: str,
    profile: str,
    parent_project: str,
    parent_profile: str,
    password: Optional[str] = None,
    parent_password: Optional[str] = None,
    overwrite: bool = False,
) -> dict:
    """Create *profile* whose vars are parent vars overridden by any existing
    child vars.  If the child profile does not yet exist the parent vars are
    used as-is."""
    parent = get_profile(parent_project, parent_profile, password=parent_password)
    if parent is None:
        raise InheritError(
            f"Parent profile '{parent_project}/{parent_profile}' not found."
        )

    child = get_profile(project, profile, password=password)
    if child is None:
        child = {}

    merged = {**parent, **child}

    add_profile(
        project,
        profile,
        merged,
        password=password,
        overwrite=True,
    )

    log_event(
        project,
        profile,
        "inherit",
        detail=f"parent={parent_project}/{parent_profile}",
    )

    return merged

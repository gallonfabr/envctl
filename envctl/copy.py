"""Copy/clone profiles between projects."""

from envctl.profile import get_profile, add_profile
from envctl.audit import log_event


def copy_profile(
    src_project: str,
    src_profile: str,
    dst_project: str,
    dst_profile: str,
    password: str | None = None,
) -> None:
    """
    Copy a profile from one project/name to another.

    Raises ValueError if the source profile does not exist.
    """
    vars_ = get_profile(src_project, src_profile, password=password)
    if vars_ is None:
        raise ValueError(
            f"Profile '{src_profile}' not found in project '{src_project}'."
        )

    add_profile(
        dst_project,
        dst_profile,
        vars_,
        password=password,
    )

    log_event(
        dst_project,
        "copy",
        {
            "src_project": src_project,
            "src_profile": src_profile,
            "dst_profile": dst_profile,
        },
    )


def rename_profile(
    project: str,
    old_name: str,
    new_name: str,
    password: str | None = None,
) -> None:
    """
    Rename a profile within a project.

    Raises ValueError if the source profile does not exist.
    """
    vars_ = get_profile(project, old_name, password=password)
    if vars_ is None:
        raise ValueError(
            f"Profile '{old_name}' not found in project '{project}'."
        )

    add_profile(project, new_name, vars_, password=password)

    from envctl.profile import delete_profile
    delete_profile(project, old_name)

    log_event(project, "rename", {"old_name": old_name, "new_name": new_name})

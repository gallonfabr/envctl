"""Clone profiles across projects."""
from envctl.profile import get_profile, add_profile
from envctl.audit import log_event
from envctl.validate import validate_profile_name, validate_project_name


def clone_profile(src_project: str, src_profile: str, dst_project: str, dst_profile: str, password: str | None = None) -> dict:
    """Clone a profile from one project to another."""
    validate_project_name(src_project)
    validate_project_name(dst_project)
    validate_profile_name(src_profile)
    validate_profile_name(dst_profile)

    data = get_profile(src_project, src_profile, password=password)
    if data is None:
        raise KeyError(f"Profile '{src_profile}' not found in project '{src_project}'")

    add_profile(dst_project, dst_profile, data, password=password)
    log_event("clone", dst_project, dst_profile, meta={
        "src_project": src_project,
        "src_profile": src_profile,
    })
    return data


def mirror_project(src_project: str, dst_project: str, profiles: list[str], password: str | None = None) -> list[str]:
    """Clone multiple profiles from one project to another. Returns list of cloned profile names."""
    validate_project_name(src_project)
    validate_project_name(dst_project)
    cloned = []
    for profile in profiles:
        clone_profile(src_project, profile, dst_project, profile, password=password)
        cloned.append(profile)
    return cloned

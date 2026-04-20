"""Priority ordering for profiles within a project."""

from typing import List
from envctl.storage import load_profiles, save_profiles


class PriorityError(Exception):
    pass


def _meta(profiles: dict, project: str, profile: str) -> dict:
    return profiles.setdefault(project, {}).setdefault(profile, {})


def set_priority(project: str, profile: str, priority: int) -> None:
    """Set a numeric priority for a profile (lower = higher priority)."""
    if priority < 0:
        raise PriorityError("Priority must be a non-negative integer.")
    profiles = load_profiles()
    if project not in profiles or profile not in profiles[project]:
        raise PriorityError(f"Profile '{profile}' not found in project '{project}'.")
    profiles[project][profile]["_priority"] = priority
    save_profiles(profiles)


def get_priority(project: str, profile: str) -> int:
    """Return the priority of a profile, defaulting to 0."""
    profiles = load_profiles()
    if project not in profiles or profile not in profiles[project]:
        raise PriorityError(f"Profile '{profile}' not found in project '{project}'.")
    return profiles[project][profile].get("_priority", 0)


def clear_priority(project: str, profile: str) -> None:
    """Remove explicit priority from a profile (resets to default 0)."""
    profiles = load_profiles()
    if project not in profiles or profile not in profiles[project]:
        raise PriorityError(f"Profile '{profile}' not found in project '{project}'.")
    profiles[project][profile].pop("_priority", None)
    save_profiles(profiles)


def ranked_profiles(project: str) -> List[str]:
    """Return profile names sorted by priority ascending (lowest number first)."""
    profiles = load_profiles()
    if project not in profiles:
        raise PriorityError(f"Project '{project}' not found.")
    project_profiles = profiles[project]
    return sorted(
        project_profiles.keys(),
        key=lambda name: project_profiles[name].get("_priority", 0),
    )

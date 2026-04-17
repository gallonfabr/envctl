"""Pin a profile as the default for a project."""

from envctl.storage import load_profiles, save_profiles
from envctl.audit import log_event


def pin_profile(project: str, profile: str) -> None:
    """Set profile as the pinned default for project."""
    store = load_profiles()
    if project not in store:
        raise KeyError(f"Project '{project}' not found")
    if profile not in store[project]:
        raise KeyError(f"Profile '{profile}' not found in project '{project}'")
    store[project]["__pinned__"] = profile
    save_profiles(store)
    log_event(project, profile, "pin")


def unpin_profile(project: str) -> None:
    """Remove the pinned default for project."""
    store = load_profiles()
    if project not in store:
        raise KeyError(f"Project '{project}' not found")
    if "__pinned__" not in store[project]:
        raise ValueError(f"No pinned profile for project '{project}'")
    removed = store[project].pop("__pinned__")
    save_profiles(store)
    log_event(project, removed, "unpin")


def get_pinned(project: str) -> str | None:
    """Return the pinned profile name for project, or None."""
    store = load_profiles()
    if project not in store:
        raise KeyError(f"Project '{project}' not found")
    return store[project].get("__pinned__")

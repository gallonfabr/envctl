"""Shadow profiles: maintain a hidden copy of a profile for safe experimentation."""

from __future__ import annotations

from typing import Optional

from envctl.profile import add_profile, get_profile, delete_profile
from envctl.audit import log_event
from envctl.storage import load_profiles, save_profiles

SHADOW_PREFIX = "__shadow__"


class ShadowError(Exception):
    pass


def _shadow_name(profile: str) -> str:
    return f"{SHADOW_PREFIX}{profile}"


def create_shadow(project: str, profile: str, password: Optional[str] = None) -> str:
    """Create a shadow copy of *profile* inside *project*.

    Returns the shadow profile name.
    """
    src = get_profile(project, profile, password=password)
    if src is None:
        raise ShadowError(f"Profile '{profile}' not found in project '{project}'")

    shadow = _shadow_name(profile)
    add_profile(project, shadow, src, password=password)
    log_event(project, profile, "shadow_created", {"shadow": shadow})
    return shadow


def promote_shadow(project: str, profile: str, password: Optional[str] = None) -> None:
    """Overwrite *profile* with its shadow copy, then remove the shadow."""
    shadow = _shadow_name(profile)
    shadow_vars = get_profile(project, shadow, password=password)
    if shadow_vars is None:
        raise ShadowError(f"No shadow found for '{profile}' in project '{project}'")

    add_profile(project, profile, shadow_vars, password=password)
    delete_profile(project, shadow)
    log_event(project, profile, "shadow_promoted", {"shadow": shadow})


def discard_shadow(project: str, profile: str) -> None:
    """Delete the shadow copy without touching the original profile."""
    shadow = _shadow_name(profile)
    profiles = load_profiles(project)
    if shadow not in profiles:
        raise ShadowError(f"No shadow found for '{profile}' in project '{project}'")
    delete_profile(project, shadow)
    log_event(project, profile, "shadow_discarded", {"shadow": shadow})


def has_shadow(project: str, profile: str) -> bool:
    """Return True if a shadow copy exists for *profile*."""
    profiles = load_profiles(project)
    return _shadow_name(profile) in profiles


def list_shadows(project: str) -> list[str]:
    """Return the original profile names that currently have a shadow."""
    profiles = load_profiles(project)
    return [
        name[len(SHADOW_PREFIX):]
        for name in profiles
        if name.startswith(SHADOW_PREFIX)
    ]

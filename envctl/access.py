"""Access control: restrict which users/roles can read or apply a profile."""
from __future__ import annotations

import os
from typing import List, Optional

from envctl.storage import load_profiles, save_profiles


class AccessError(Exception):
    pass


def _meta(project: str, profile: str, profiles: dict) -> dict:
    return profiles.get(project, {}).get(profile, {})


def set_allowed_users(
    project: str, profile: str, users: List[str]
) -> None:
    """Set the list of users permitted to access a profile."""
    profiles = load_profiles()
    if project not in profiles or profile not in profiles[project]:
        raise AccessError(f"Profile '{project}/{profile}' not found.")
    profiles[project][profile]["allowed_users"] = list(users)
    save_profiles(profiles)


def get_allowed_users(project: str, profile: str) -> Optional[List[str]]:
    """Return allowed users list, or None if unrestricted."""
    profiles = load_profiles()
    meta = _meta(project, profile, profiles)
    return meta.get("allowed_users", None)


def clear_allowed_users(project: str, profile: str) -> None:
    """Remove access restrictions from a profile (make it unrestricted)."""
    profiles = load_profiles()
    if project not in profiles or profile not in profiles[project]:
        raise AccessError(f"Profile '{project}/{profile}' not found.")
    profiles[project][profile].pop("allowed_users", None)
    save_profiles(profiles)


def assert_access(project: str, profile: str, user: Optional[str] = None) -> None:
    """Raise AccessError if *user* is not permitted to access the profile.

    If no allowed_users list is set the profile is unrestricted.
    Falls back to the current OS user when *user* is not supplied.
    """
    allowed = get_allowed_users(project, profile)
    if allowed is None:
        return  # unrestricted
    current = user or os.environ.get("USER") or os.environ.get("USERNAME", "")
    if current not in allowed:
        raise AccessError(
            f"User '{current}' is not allowed to access '{project}/{profile}'."
        )


def list_restricted_profiles(project: str) -> List[str]:
    """Return profile names that have an explicit allowed_users list."""
    profiles = load_profiles()
    result = []
    for name, data in profiles.get(project, {}).items():
        if "allowed_users" in data:
            result.append(name)
    return result

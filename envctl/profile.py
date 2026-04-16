"""Profile management: add, get, delete, and apply environment profiles."""

from __future__ import annotations

from typing import Optional

from envctl import storage
from envctl.crypto import encrypt_vars, decrypt_vars


def add_profile(
    project: str,
    profile: str,
    vars_dict: dict,
    password: Optional[str] = None,
) -> None:
    """Add or overwrite a profile for a project."""
    profiles = storage.load_profiles()
    profiles.setdefault(project, {})

    if password:
        entry = {"encrypted": True, **encrypt_vars(vars_dict, password)}
    else:
        entry = {"encrypted": False, "vars": vars_dict}

    profiles[project][profile] = entry
    storage.save_profiles(profiles)


def get_profile(
    project: str,
    profile: str,
    password: Optional[str] = None,
) -> dict:
    """Retrieve env vars for a profile. Decrypts if necessary."""
    profiles = storage.load_profiles()
    try:
        entry = profiles[project][profile]
    except KeyError:
        raise KeyError(f"Profile '{profile}' not found for project '{project}'.")

    if entry.get("encrypted"):
        if not password:
            raise ValueError("Password required to decrypt this profile.")
        return decrypt_vars(entry, password)
    return entry["vars"]


def delete_profile(project: str, profile: str) -> None:
    """Delete a profile. Removes the project key if no profiles remain."""
    profiles = storage.load_profiles()
    if project not in profiles or profile not in profiles[project]:
        raise KeyError(f"Profile '{profile}' not found for project '{project}'.")
    del profiles[project][profile]
    if not profiles[project]:
        del profiles[project]
    storage.save_profiles(profiles)


def apply_profile(
    project: str,
    profile: str,
    password: Optional[str] = None,
) -> dict:
    """Return env vars ready to be exported to the shell environment."""
    vars_dict = get_profile(project, profile, password)
    return {k: str(v) for k, v in vars_dict.items()}

"""Profile management: add, get, delete, apply."""

from typing import Optional
from envctl.storage import load_profiles, save_profiles
from envctl.crypto import encrypt_vars, decrypt_vars
from envctl.audit import log_event


def add_profile(project: str, profile: str, variables: dict, password: Optional[str] = None) -> None:
    """Add or overwrite a profile for a project."""
    store = load_profiles()
    store.setdefault(project, {})
    if password:
        entry = {"encrypted": True, "data": encrypt_vars(variables, password)}
    else:
        entry = {"encrypted": False, "data": variables}
    store[project][profile] = entry
    save_profiles(store)
    log_ profile, extra={"encrypted": bool(password)})


def get_profile(project: str, profile: str, password: Optional[str] = None) -> dict:
    """Retrieve variables for a profile."""
    store = load_profiles()
    project_data = store.get(project, {})
    if profile not in project_data:
        raise KeyError(f"Profile '{profile}' not found for project '{project}'.")
    entry = project_data[profile]
    log_event("get", project, profile)
    if entry["encrypted"]:
        if not password:
            raise ValueError("Password required to decrypt this profile.")
        return decrypt_vars(entry["data"], password)
    return entry["data"]


def delete_profile(project: str, profile: str) -> None:
    """Delete a profile."""
    store = load_profiles()
    if project not in store or profile not in store[project]:
        raise KeyError(f"Profile '{profile}' not found for project '{project}'.")
    del store[project][profile]
    if not store[project]:
        del store[project]
    save_profiles(store)
    log_event("delete", project, profile)


def apply_profile(project: str, profile: str, password: Optional[str] = None) -> dict:
    """Return variables intended for shell export."""
    variables = get_profile(project, profile, password=password)
    log_event("apply", project, profile)
    return variables

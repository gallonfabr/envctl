"""Group multiple profiles under a named group for batch operations."""
from __future__ import annotations
from envctl.storage import load_profiles, save_profiles
from envctl.audit import log_event


class GroupError(Exception):
    pass


def _groups(data: dict) -> dict:
    return data.setdefault("__groups__", {})


def create_group(group: str, members: list[tuple[str, str]]) -> None:
    """Create a named group of (project, profile) pairs."""
    if not group:
        raise GroupError("Group name must not be empty.")
    data = load_profiles()
    for project, profile in members:
        proj_data = data.get(project, {})
        if profile not in proj_data:
            raise GroupError(f"Profile '{profile}' not found in project '{project}'.")
    _groups(data)[group] = [{"project": p, "profile": pr} for p, pr in members]
    save_profiles(data)
    log_event("group_create", "__groups__", group, {"members": members})


def delete_group(group: str) -> None:
    data = load_profiles()
    groups = _groups(data)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    del groups[group]
    save_profiles(data)
    log_event("group_delete", "__groups__", group, {})


def get_group(group: str) -> list[dict]:
    data = load_profiles()
    groups = _groups(data)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    return groups[group]


def list_groups() -> list[str]:
    data = load_profiles()
    return list(_groups(data).keys())


def add_to_group(group: str, project: str, profile: str) -> None:
    data = load_profiles()
    groups = _groups(data)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    proj_data = data.get(project, {})
    if profile not in proj_data:
        raise GroupError(f"Profile '{profile}' not found in project '{project}'.")
    entry = {"project": project, "profile": profile}
    if entry not in groups[group]:
        groups[group].append(entry)
    save_profiles(data)
    log_event("group_add_member", project, profile, {"group": group})


def remove_from_group(group: str, project: str, profile: str) -> None:
    data = load_profiles()
    groups = _groups(data)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    entry = {"project": project, "profile": profile}
    if entry not in groups[group]:
        raise GroupError(f"Member not found in group '{group}'.")
    groups[group].remove(entry)
    save_profiles(data)
    log_event("group_remove_member", project, profile, {"group": group})

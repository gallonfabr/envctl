"""Snapshot support: capture and restore environment variable profiles."""

from datetime import datetime
from envctl.storage import load_profiles, save_profiles

SNAPSHOT_PROJECT = "__snapshots__"


def _snapshot_key(project: str, profile: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    return f"{project}__{profile}__{timestamp}"


def create_snapshot(project: str, profile: str) -> str:
    """Snapshot a profile. Returns the snapshot key."""
    profiles = load_profiles()
    source = profiles.get(project, {}).get(profile)
    if source is None:
        raise KeyError(f"Profile '{profile}' not found in project '{project}'")

    key = _snapshot_key(project, profile)
    snapshots = profiles.setdefault(SNAPSHOT_PROJECT, {})
    snapshots[key] = dict(source)
    save_profiles(profiles)
    return key


def list_snapshots(project: str = None) -> list[dict]:
    """List snapshots, optionally filtered by source project."""
    profiles = load_profiles()
    snapshots = profiles.get(SNAPSHOT_PROJECT, {})
    result = []
    for key, data in snapshots.items():
        parts = key.split("__")
        src_project = parts[0] if len(parts) >= 3 else ""
        src_profile = parts[1] if len(parts) >= 3 else ""
        timestamp = parts[2] if len(parts) >= 3 else ""
        if project is None or src_project == project:
            result.append({
                "key": key,
                "project": src_project,
                "profile": src_profile,
                "timestamp": timestamp,
                "data": data,
            })
    return result


def restore_snapshot(snapshot_key: str, target_project: str, target_profile: str) -> None:
    """Restore a snapshot into a given project/profile."""
    profiles = load_profiles()
    snapshots = profiles.get(SNAPSHOT_PROJECT, {})
    if snapshot_key not in snapshots:
        raise KeyError(f"Snapshot '{snapshot_key}' not found")
    profiles.setdefault(target_project, {})[target_profile] = dict(snapshots[snapshot_key])
    save_profiles(profiles)


def delete_snapshot(snapshot_key: str) -> None:
    """Delete a snapshot by key."""
    profiles = load_profiles()
    snapshots = profiles.get(SNAPSHOT_PROJECT, {})
    if snapshot_key not in snapshots:
        raise KeyError(f"Snapshot '{snapshot_key}' not found")
    del snapshots[snapshot_key]
    save_profiles(profiles)

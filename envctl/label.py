"""Label management for environment profiles.

Labels are free-form key=value metadata attached to a profile,
distinct from tags (which are plain strings) and memos (single text).
"""
from __future__ import annotations

from typing import Dict, Optional

from envctl.storage import load_profiles, save_profiles


class LabelError(Exception):
    pass


def _meta(project: str, profile: str) -> dict:
    profiles = load_profiles(project)
    if profile not in profiles:
        raise LabelError(f"Profile '{profile}' not found in project '{project}'")
    return profiles


def set_label(project: str, profile: str, key: str, value: str) -> None:
    """Set a label key=value on a profile."""
    if not key or not key.isidentifier():
        raise LabelError(f"Invalid label key: '{key}'")
    if value is None:
        raise LabelError("Label value must not be None")
    profiles = _meta(project, profile)
    labels = profiles[profile].setdefault("labels", {})
    labels[key] = value
    save_profiles(project, profiles)


def remove_label(project: str, profile: str, key: str) -> None:
    """Remove a label key from a profile."""
    profiles = _meta(project, profile)
    labels = profiles[profile].get("labels", {})
    if key not in labels:
        raise LabelError(f"Label '{key}' not found on profile '{profile}'")
    del labels[key]
    profiles[profile]["labels"] = labels
    save_profiles(project, profiles)


def get_labels(project: str, profile: str) -> Dict[str, str]:
    """Return all labels for a profile."""
    profiles = _meta(project, profile)
    return dict(profiles[profile].get("labels", {}))


def find_by_label(project: str, key: str, value: Optional[str] = None) -> list[str]:
    """Find profiles in a project that have the given label key (and optionally value)."""
    profiles = load_profiles(project)
    results = []
    for name, data in profiles.items():
        labels = data.get("labels", {})
        if key in labels:
            if value is None or labels[key] == value:
                results.append(name)
    return sorted(results)


def clear_labels(project: str, profile: str) -> None:
    """Remove all labels from a profile."""
    profiles = _meta(project, profile)
    profiles[profile]["labels"] = {}
    save_profiles(project, profiles)

"""Retention policy: automatically purge profiles older than N days based on last-applied history."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from envctl.storage import load_profiles, save_profiles
from envctl.history import get_history
from envctl.audit import log_event


class RetentionError(Exception):
    pass


_META_KEY = "__retention__"


def _meta(profiles: dict, project: str) -> dict:
    return profiles.setdefault(project, {}).setdefault(_META_KEY, {})


def set_retention(project: str, days: int) -> None:
    """Set a retention policy (in days) for a project."""
    if days <= 0:
        raise RetentionError("Retention days must be a positive integer.")
    profiles = load_profiles()
    _meta(profiles, project)["days"] = days
    save_profiles(profiles)


def get_retention(project: str) -> Optional[int]:
    """Return the retention policy in days, or None if not set."""
    profiles = load_profiles()
    return profiles.get(project, {}).get(_META_KEY, {}).get("days")


def clear_retention(project: str) -> None:
    """Remove the retention policy for a project."""
    profiles = load_profiles()
    if project in profiles and _META_KEY in profiles[project]:
        del profiles[project][_META_KEY]
        save_profiles(profiles)


def apply_retention(project: str, dry_run: bool = False) -> list[str]:
    """Purge profiles not applied within the retention window.

    Returns the list of profile names that were (or would be) deleted.
    """
    days = get_retention(project)
    if days is None:
        raise RetentionError(f"No retention policy set for project '{project}'.")

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    profiles = load_profiles()
    project_profiles = {
        k: v for k, v in profiles.get(project, {}).items() if not k.startswith("__")
    }

    purged: list[str] = []
    for profile_name in list(project_profiles.keys()):
        history = get_history(project, profile_name, limit=1)
        if not history:
            last_applied = None
        else:
            last_applied = datetime.fromisoformat(history[0]["applied_at"])

        if last_applied is None or last_applied < cutoff:
            purged.append(profile_name)
            if not dry_run:
                del profiles[project][profile_name]
                log_event("retention_purge", project, profile_name)

    if purged and not dry_run:
        save_profiles(profiles)

    return purged

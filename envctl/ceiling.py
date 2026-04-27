"""Ceiling: enforce a maximum number of profiles per project."""

from __future__ import annotations

from envctl.storage import load_profiles, save_profiles, list_profiles


class CeilingError(Exception):
    """Raised when a ceiling constraint is violated or misconfigured."""


_CEILING_KEY = "__ceiling__"


def _meta(project: str) -> dict:
    data = load_profiles()
    return data.setdefault(project, {}).setdefault(_CEILING_KEY, {})


def set_ceiling(project: str, limit: int) -> None:
    """Set the maximum number of profiles allowed for *project*."""
    if limit < 1:
        raise CeilingError("Ceiling limit must be a positive integer.")
    data = load_profiles()
    data.setdefault(project, {})[_CEILING_KEY] = {"limit": limit}
    save_profiles(data)


def remove_ceiling(project: str) -> None:
    """Remove the ceiling constraint for *project*."""
    data = load_profiles()
    if project in data and _CEILING_KEY in data[project]:
        del data[project][_CEILING_KEY]
        save_profiles(data)


def get_ceiling(project: str) -> int | None:
    """Return the ceiling limit for *project*, or None if unset."""
    data = load_profiles()
    entry = data.get(project, {}).get(_CEILING_KEY)
    if entry is None:
        return None
    return entry.get("limit")


def check_ceiling(project: str) -> None:
    """Raise *CeilingError* if adding one more profile would exceed the ceiling."""
    limit = get_ceiling(project)
    if limit is None:
        return
    current = len(
        [p for p in list_profiles(project) if not p.startswith("__")]
    )
    if current >= limit:
        raise CeilingError(
            f"Project '{project}' has reached its profile ceiling of {limit}."
        )


def ceiling_status(project: str) -> dict:
    """Return a dict with ceiling info for *project*."""
    limit = get_ceiling(project)
    used = len([p for p in list_profiles(project) if not p.startswith("__")])
    return {
        "project": project,
        "limit": limit,
        "used": used,
        "available": (limit - used) if limit is not None else None,
    }

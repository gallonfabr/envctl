"""Quota enforcement: limit the number of profiles per project."""

from envctl.storage import load_profiles, save_profiles, list_profiles

QUOTA_KEY = "__quota__"
DEFAULT_QUOTA = None  # None means unlimited


class QuotaError(Exception):
    pass


def set_quota(project: str, limit: int) -> None:
    """Set the maximum number of profiles allowed for a project."""
    if limit < 1:
        raise QuotaError("Quota limit must be a positive integer.")
    data = load_profiles()
    if project not in data:
        data[project] = {}
    data[project][QUOTA_KEY] = limit
    save_profiles(data)


def remove_quota(project: str) -> None:
    """Remove the quota restriction for a project."""
    data = load_profiles()
    if project in data and QUOTA_KEY in data[project]:
        del data[project][QUOTA_KEY]
        save_profiles(data)


def get_quota(project: str) -> int | None:
    """Return the quota limit for a project, or None if unlimited."""
    data = load_profiles()
    return data.get(project, {}).get(QUOTA_KEY, DEFAULT_QUOTA)


def check_quota(project: str) -> None:
    """Raise QuotaError if adding a new profile would exceed the project quota."""
    limit = get_quota(project)
    if limit is None:
        return
    current = len(
        [p for p in list_profiles(project) if p != QUOTA_KEY]
    )
    if current >= limit:
        raise QuotaError(
            f"Project '{project}' has reached its profile quota of {limit}."
        )


def quota_status(project: str) -> dict:
    """Return a dict with quota info: limit, used, available."""
    limit = get_quota(project)
    used = len([p for p in list_profiles(project) if p != QUOTA_KEY])
    return {
        "project": project,
        "limit": limit,
        "used": used,
        "available": (limit - used) if limit is not None else None,
    }

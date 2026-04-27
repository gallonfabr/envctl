"""quota_guard.py — enforce profile-count and variable-count quotas before mutations."""
from __future__ import annotations

from envctl.quota import QuotaError, get_quota, check_quota
from envctl.storage import load_profiles, list_profiles


class QuotaGuardError(QuotaError):
    """Raised when a quota would be exceeded by a proposed mutation."""


def guard_add_profile(project: str) -> None:
    """Raise QuotaGuardError if adding one more profile would exceed the project quota."""
    quota = get_quota(project)
    if quota is None:
        return
    current = len(list_profiles(project))
    if current >= quota:
        raise QuotaGuardError(
            f"Project '{project}' has reached its profile quota ({quota}). "
            "Remove a profile or raise the quota before adding a new one."
        )


def guard_add_vars(project: str, profile: str, new_vars: dict) -> None:
    """Raise QuotaGuardError if adding *new_vars* would exceed the per-profile variable quota.

    The per-profile variable quota is stored under the key ``<project>/<profile>``.
    Falls back to checking the project-level quota when no profile-level quota is set.
    """
    scoped_key = f"{project}/{profile}"
    quota = get_quota(scoped_key)
    if quota is None:
        quota = get_quota(project)
    if quota is None:
        return

    profiles = load_profiles(project)
    existing: dict = profiles.get(profile, {}).get("vars", {})
    merged_count = len({**existing, **new_vars})
    if merged_count > quota:
        raise QuotaGuardError(
            f"Profile '{profile}' in project '{project}' would have {merged_count} variables, "
            f"exceeding the quota of {quota}."
        )


def quota_status(project: str) -> dict:
    """Return a summary dict with quota and current usage for *project*."""
    quota = get_quota(project)
    current = len(list_profiles(project))
    return {
        "project": project,
        "quota": quota,
        "used": current,
        "available": (quota - current) if quota is not None else None,
        "exceeded": (current > quota) if quota is not None else False,
    }

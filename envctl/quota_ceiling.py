"""quota_ceiling.py — enforce a hard ceiling on the number of vars per profile.

Combines quota_guard logic with ceiling constraints to provide a unified
guard that checks both project-level quotas and per-profile var ceilings.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envctl.ceiling import get_ceiling, CeilingError
from envctl.quota import get_quota, check_quota, QuotaError
from envctl.storage import load_profiles


class QuotaCeilingError(Exception):
    """Raised when a quota or ceiling constraint is violated."""


@dataclass
class GuardResult:
    allowed: bool
    reason: Optional[str] = None


def check_var_ceiling(project: str, profile: str, incoming: int) -> GuardResult:
    """Return GuardResult indicating whether adding *incoming* vars is allowed.

    Checks the per-profile ceiling (max vars) stored in envctl.ceiling.
    """
    ceiling = get_ceiling(project, profile)
    if ceiling is None:
        return GuardResult(allowed=True)

    profiles = load_profiles(project)
    if profile not in profiles:
        raise QuotaCeilingError(f"Profile '{profile}' not found in project '{project}'")

    current = len(profiles[profile].get("vars", {}))
    if current + incoming > ceiling:
        return GuardResult(
            allowed=False,
            reason=(
                f"Adding {incoming} var(s) would exceed ceiling of {ceiling} "
                f"(currently {current})"
            ),
        )
    return GuardResult(allowed=True)


def check_project_quota(project: str) -> GuardResult:
    """Return GuardResult indicating whether adding a new profile is allowed.

    Checks the project-level quota stored in envctl.quota.
    """
    try:
        check_quota(project)
        return GuardResult(allowed=True)
    except QuotaError as exc:
        return GuardResult(allowed=False, reason=str(exc))


def enforce_var_ceiling(project: str, profile: str, incoming: int) -> None:
    """Raise QuotaCeilingError if ceiling would be exceeded."""
    result = check_var_ceiling(project, profile, incoming)
    if not result.allowed:
        raise QuotaCeilingError(result.reason)


def enforce_project_quota(project: str) -> None:
    """Raise QuotaCeilingError if project quota would be exceeded."""
    result = check_project_quota(project)
    if not result.allowed:
        raise QuotaCeilingError(result.reason)

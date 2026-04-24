"""Stale profile detection — flag profiles that haven't been applied recently."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from envctl.history import get_history
from envctl.storage import list_projects, list_profiles


class StaleError(Exception):
    """Raised when stale detection cannot be performed."""


@dataclass
class StaleProfile:
    project: str
    profile: str
    last_applied: Optional[datetime]
    days_idle: Optional[float]


def _last_applied(project: str, profile: str) -> Optional[datetime]:
    """Return the most recent apply timestamp for a profile, or None."""
    entries = get_history(project, profile, limit=1)
    if not entries:
        return None
    ts = entries[0].get("timestamp")
    if ts is None:
        return None
    return datetime.fromisoformat(ts)


def find_stale(
    project: str,
    threshold_days: float = 30.0,
    *,
    include_never_applied: bool = True,
) -> List[StaleProfile]:
    """Return profiles in *project* that are stale (idle >= threshold_days).

    Args:
        project: Project name to scan.
        threshold_days: Minimum idle days to be considered stale.
        include_never_applied: Whether profiles with no apply history count.

    Raises:
        StaleError: If *project* does not exist.
    """
    projects = list_projects()
    if project not in projects:
        raise StaleError(f"Project '{project}' not found.")

    now = datetime.now(tz=timezone.utc)
    stale: List[StaleProfile] = []

    for profile in list_profiles(project):
        last = _last_applied(project, profile)
        if last is None:
            if include_never_applied:
                stale.append(StaleProfile(project, profile, None, None))
            continue
        # Ensure tz-aware comparison
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        idle = (now - last).total_seconds() / 86400.0
        if idle >= threshold_days:
            stale.append(StaleProfile(project, profile, last, round(idle, 2)))

    return stale


def stale_summary(stale: List[StaleProfile]) -> str:
    """Return a human-readable summary of stale profiles."""
    if not stale:
        return "No stale profiles found."
    lines = [f"{'Profile':<30} {'Last Applied':<26} Days Idle"]
    lines.append("-" * 65)
    for s in stale:
        last_str = s.last_applied.isoformat(timespec="seconds") if s.last_applied else "never"
        idle_str = str(s.days_idle) if s.days_idle is not None else "—"
        lines.append(f"{s.profile:<30} {last_str:<26} {idle_str}")
    return "\n".join(lines)

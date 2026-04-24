"""Track and report variable-level change trends across profile history."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envctl.audit import read_events
from envctl.profile import get_profile
from envctl.storage import list_profiles


class TrendError(Exception):
    """Raised when trend analysis cannot be completed."""


@dataclass
class VarTrend:
    key: str
    change_count: int
    last_value: Optional[str]
    first_seen: Optional[str]  # ISO timestamp
    last_changed: Optional[str]  # ISO timestamp
    direction: str = "stable"  # rising | declining | stable | volatile


@dataclass
class ProfileTrend:
    project: str
    profile: str
    total_applies: int
    var_trends: List[VarTrend] = field(default_factory=list)


def _direction(change_count: int, total_applies: int) -> str:
    if total_applies == 0:
        return "stable"
    ratio = change_count / total_applies
    if ratio == 0:
        return "stable"
    if ratio >= 0.6:
        return "volatile"
    if ratio >= 0.3:
        return "rising"
    return "declining"


def analyze_profile_trend(
    project: str,
    profile: str,
    password: Optional[str] = None,
    limit: int = 50,
) -> ProfileTrend:
    """Analyse how individual variables in *profile* have changed over time."""
    try:
        current = get_profile(project, profile, password=password)
    except Exception as exc:  # noqa: BLE001
        raise TrendError(str(exc)) from exc

    events = read_events(project=project, limit=limit)
    apply_events = [e for e in events if e.get("action") == "apply" and e.get("profile") == profile]
    total_applies = len(apply_events)

    # Count how many apply events mention each key changing (use snapshots in meta if available)
    change_counts: Dict[str, int] = {k: 0 for k in current}
    first_seen: Dict[str, str] = {}
    last_changed: Dict[str, str] = {}

    for event in apply_events:
        changed_keys = event.get("changed_keys") or []
        ts = event.get("timestamp", "")
        for key in changed_keys:
            if key in change_counts:
                change_counts[key] += 1
                last_changed[key] = ts
            if key not in first_seen and ts:
                first_seen[key] = ts

    var_trends = [
        VarTrend(
            key=k,
            change_count=change_counts[k],
            last_value=v,
            first_seen=first_seen.get(k),
            last_changed=last_changed.get(k),
            direction=_direction(change_counts[k], total_applies),
        )
        for k, v in current.items()
    ]

    return ProfileTrend(
        project=project,
        profile=profile,
        total_applies=total_applies,
        var_trends=sorted(var_trends, key=lambda t: t.change_count, reverse=True),
    )


def top_volatile_vars(project: str, profile: str, n: int = 5, password: Optional[str] = None) -> List[VarTrend]:
    """Return the *n* most frequently changed variables in a profile."""
    trend = analyze_profile_trend(project, profile, password=password)
    return trend.var_trends[:n]

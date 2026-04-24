"""Profile insight: surface quick stats and health signals for a project's profiles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envctl.storage import list_profiles, load_profiles
from envctl.lock import is_locked
from envctl.expire import is_expired, get_expiry
from envctl.pin import get_pinned
from envctl.audit import search_events


class InsightError(Exception):
    pass


@dataclass
class ProfileInsight:
    project: str
    profile: str
    var_count: int
    is_locked: bool
    is_expired: bool
    is_pinned: bool
    expiry: Optional[str]
    recent_applies: int
    tags: List[str] = field(default_factory=list)


@dataclass
class ProjectInsight:
    project: str
    profile_count: int
    total_vars: int
    locked_count: int
    expired_count: int
    pinned_profile: Optional[str]
    profiles: List[ProfileInsight] = field(default_factory=list)


def _recent_applies(project: str, profile: str, limit: int = 30) -> int:
    events = search_events(project=project, limit=limit)
    return sum(
        1 for e in events
        if e.get("event") == "apply" and e.get("profile") == profile
    )


def profile_insight(project: str, profile: str) -> ProfileInsight:
    store = load_profiles()
    if project not in store or profile not in store[project]:
        raise InsightError(f"Profile '{project}/{profile}' not found.")
    data = store[project][profile]
    vars_data = data.get("vars", {})
    pinned = get_pinned(project)
    expiry = get_expiry(project, profile)
    return ProfileInsight(
        project=project,
        profile=profile,
        var_count=len(vars_data),
        is_locked=is_locked(project, profile),
        is_expired=is_expired(project, profile),
        is_pinned=(pinned == profile),
        expiry=expiry,
        recent_applies=_recent_applies(project, profile),
        tags=data.get("tags", []),
    )


def project_insight(project: str) -> ProjectInsight:
    profiles = list_profiles(project)
    if profiles is None:
        raise InsightError(f"Project '{project}' not found.")
    insights = [profile_insight(project, p) for p in profiles]
    return ProjectInsight(
        project=project,
        profile_count=len(insights),
        total_vars=sum(i.var_count for i in insights),
        locked_count=sum(1 for i in insights if i.is_locked),
        expired_count=sum(1 for i in insights if i.is_expired),
        pinned_profile=get_pinned(project),
        profiles=insights,
    )

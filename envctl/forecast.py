"""Forecast profile usage trends based on apply history."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from envctl.history import get_history
from envctl.storage import list_projects, list_profiles


class ForecastError(Exception):
    """Raised when forecast cannot be computed."""


@dataclass
class ProfileUsage:
    project: str
    profile: str
    total_applies: int
    applies_last_7d: int
    applies_last_30d: int
    last_applied: Optional[str]
    trend: str  # "rising", "stable", "declining", "inactive"


def _trend(last_7d: int, last_30d: int) -> str:
    if last_30d == 0:
        return "inactive"
    weekly_avg = last_30d / 4.0
    if last_7d >= weekly_avg * 1.5:
        return "rising"
    if last_7d <= weekly_avg * 0.5:
        return "declining"
    return "stable"


def forecast_project(project: str, days: int = 30) -> List[ProfileUsage]:
    """Return usage forecast for all profiles in a project."""
    profiles = list_profiles(project)
    if not profiles:
        raise ForecastError(f"No profiles found for project '{project}'")

    now = datetime.utcnow()
    cutoff_30d = now - timedelta(days=30)
    cutoff_7d = now - timedelta(days=7)

    results: List[ProfileUsage] = []
    for profile_name in profiles:
        history = get_history(project, profile_name)
        total = len(history)
        last_30d_entries = [
            e for e in history
            if datetime.fromisoformat(e["applied_at"]) >= cutoff_30d
        ]
        last_7d_entries = [
            e for e in last_30d_entries
            if datetime.fromisoformat(e["applied_at"]) >= cutoff_7d
        ]
        last_applied = history[0]["applied_at"] if history else None
        results.append(ProfileUsage(
            project=project,
            profile=profile_name,
            total_applies=total,
            applies_last_7d=len(last_7d_entries),
            applies_last_30d=len(last_30d_entries),
            last_applied=last_applied,
            trend=_trend(len(last_7d_entries), len(last_30d_entries)),
        ))

    results.sort(key=lambda u: u.applies_last_30d, reverse=True)
    return results


def top_profiles(n: int = 5) -> List[ProfileUsage]:
    """Return the top N most-used profiles across all projects."""
    all_usage: List[ProfileUsage] = []
    for project in list_projects():
        try:
            all_usage.extend(forecast_project(project))
        except ForecastError:
            continue
    all_usage.sort(key=lambda u: u.applies_last_30d, reverse=True)
    return all_usage[:n]

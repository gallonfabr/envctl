"""Track consecutive-day apply streaks for profiles."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from envctl.storage import get_store_path


class StreakError(Exception):
    pass


@dataclass
class StreakInfo:
    project: str
    profile: str
    current: int
    longest: int
    last_applied: Optional[str]  # ISO date string


def _get_path() -> Path:
    p = get_store_path().parent / "streaks.json"
    return p


def _load() -> dict:
    p = _get_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(data: dict) -> None:
    _get_path().write_text(json.dumps(data, indent=2))


def _key(project: str, profile: str) -> str:
    return f"{project}::{profile}"


def record_apply(project: str, profile: str, today: Optional[date] = None) -> StreakInfo:
    """Record a profile apply and update streak counters."""
    if not project or not profile:
        raise StreakError("project and profile must be non-empty")

    today = today or date.today()
    data = _load()
    k = _key(project, profile)
    entry = data.get(k, {"current": 0, "longest": 0, "last_applied": None})

    last = date.fromisoformat(entry["last_applied"]) if entry["last_applied"] else None

    if last is None:
        entry["current"] = 1
    elif today == last:
        pass  # same day, no change
    elif today == last + timedelta(days=1):
        entry["current"] += 1
    else:
        entry["current"] = 1

    entry["longest"] = max(entry["longest"], entry["current"])
    entry["last_applied"] = today.isoformat()
    data[k] = entry
    _save(data)

    return StreakInfo(
        project=project,
        profile=profile,
        current=entry["current"],
        longest=entry["longest"],
        last_applied=entry["last_applied"],
    )


def get_streak(project: str, profile: str) -> StreakInfo:
    """Retrieve current streak info for a profile."""
    data = _load()
    k = _key(project, profile)
    entry = data.get(k)
    if entry is None:
        return StreakInfo(project=project, profile=profile, current=0, longest=0, last_applied=None)
    return StreakInfo(
        project=project,
        profile=profile,
        current=entry["current"],
        longest=entry["longest"],
        last_applied=entry["last_applied"],
    )


def reset_streak(project: str, profile: str) -> None:
    """Reset streak data for a profile."""
    data = _load()
    k = _key(project, profile)
    if k not in data:
        raise StreakError(f"No streak data for {project}/{profile}")
    del data[k]
    _save(data)

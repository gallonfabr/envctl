"""Schedule-based profile auto-apply support."""
from __future__ import annotations
import json
from datetime import datetime, time
from pathlib import Path
from typing import Optional

SCHEDULE_FILE = "schedules.json"

VALID_DAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
DAY_MAP = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class ScheduleError(Exception):
    pass


def _get_path() -> Path:
    from envctl.storage import get_store_path
    return get_store_path() / SCHEDULE_FILE


def _load() -> dict:
    p = _get_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(data: dict) -> None:
    _get_path().write_text(json.dumps(data, indent=2))


def set_schedule(project: str, profile: str, start: str, end: str, days: list[str]) -> dict:
    """Schedule a profile to be active during a time window on given days."""
    try:
        time.fromisoformat(start)
        time.fromisoformat(end)
    except ValueError as e:
        raise ScheduleError(f"Invalid time format: {e}")

    bad = set(d.lower() for d in days) - VALID_DAYS
    if bad:
        raise ScheduleError(f"Invalid days: {bad}")

    data = _load()
    key = f"{project}/{profile}"
    entry = {"project": project, "profile": profile, "start": start, "end": end, "days": [d.lower() for d in days]}
    data[key] = entry
    _save(data)
    return entry


def remove_schedule(project: str, profile: str) -> None:
    data = _load()
    key = f"{project}/{profile}"
    if key not in data:
        raise ScheduleError(f"No schedule for {key}")
    del data[key]
    _save(data)


def get_schedule(project: str, profile: str) -> Optional[dict]:
    return _load().get(f"{project}/{profile}")


def list_schedules(project: Optional[str] = None) -> list[dict]:
    data = _load()
    entries = list(data.values())
    if project:
        entries = [e for e in entries if e["project"] == project]
    return entries


def active_now(project: str, profile: str, at: Optional[datetime] = None) -> bool:
    """Return True if the schedule for project/profile is active at given time."""
    entry = get_schedule(project, profile)
    if not entry:
        return False
    now = at or datetime.now()
    if DAY_MAP[now.weekday()] not in entry["days"]:
        return False
    start = time.fromisoformat(entry["start"])
    end = time.fromisoformat(entry["end"])
    current = now.time().replace(second=0, microsecond=0)
    return start <= current <= end


def active_schedules(project: Optional[str] = None, at: Optional[datetime] = None) -> list[dict]:
    """Return all schedules that are currently active, optionally filtered by project."""
    now = at or datetime.now()
    return [
        entry for entry in list_schedules(project)
        if active_now(entry["project"], entry["profile"], at=now)
    ]

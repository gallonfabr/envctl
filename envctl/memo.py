"""Memo/notes feature: attach short notes to profiles."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from envctl.storage import load_profiles, save_profiles


class MemoError(Exception):
    pass


def _meta(project: str, profile: str, data: dict) -> dict:
    projects = data.get("projects", {})
    profiles = projects.get(project, {})
    if profile not in profiles:
        raise MemoError(f"Profile '{profile}' not found in project '{project}'")
    return profiles[profile].setdefault("_meta", {})


def set_memo(project: str, profile: str, text: str) -> None:
    """Attach or overwrite a memo on a profile."""
    if not text or not text.strip():
        raise MemoError("Memo text must not be empty")
    data = load_profiles()
    meta = _meta(project, profile, data)
    meta["memo"] = {
        "text": text.strip(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_profiles(data)


def get_memo(project: str, profile: str) -> Optional[dict]:
    """Return the memo dict for a profile, or None if not set."""
    data = load_profiles()
    try:
        meta = _meta(project, profile, data)
    except MemoError:
        raise
    return meta.get("memo")


def clear_memo(project: str, profile: str) -> None:
    """Remove the memo from a profile."""
    data = load_profiles()
    meta = _meta(project, profile, data)
    meta.pop("memo", None)
    save_profiles(data)


def list_memos(project: str) -> list[dict]:
    """Return all profiles in a project that have a memo attached."""
    data = load_profiles()
    projects = data.get("projects", {})
    if project not in projects:
        raise MemoError(f"Project '{project}' not found")
    results = []
    for prof_name, prof_data in projects[project].items():
        memo = prof_data.get("_meta", {}).get("memo")
        if memo:
            results.append({"profile": prof_name, **memo})
    return results

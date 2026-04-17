"""Track apply history for profiles."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envctl.storage import get_store_path


def get_history_path() -> Path:
    path = get_store_path().parent / "apply_history.json"
    return path


def _load() -> list:
    p = get_history_path()
    if not p.exists():
        return []
    with open(p) as f:
        return json.load(f)


def _save(entries: list) -> None:
    p = get_history_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(entries, f, indent=2)


def record_apply(project: str, profile: str) -> dict:
    """Record that a profile was applied."""
    entry = {
        "project": project,
        "profile": profile,
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }
    entries = _load()
    entries.append(entry)
    _save(entries)
    return entry


def get_history(
    project: Optional[str] = None,
    limit: Optional[int] = None,
) -> list:
    """Return apply history, optionally filtered by project."""
    entries = _load()
    if project:
        entries = [e for e in entries if e["project"] == project]
    entries = list(reversed(entries))
    if limit:
        entries = entries[:limit]
    return entries


def clear_history(project: Optional[str] = None) -> int:
    """Clear history. Returns number of entries removed."""
    entries = _load()
    if project:
        kept = [e for e in entries if e["project"] != project]
    else:
        kept = []
    removed = len(entries) - len(kept)
    _save(kept)
    return removed

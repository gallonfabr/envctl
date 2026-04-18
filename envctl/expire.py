"""Profile expiration: set TTL on profiles and check if they are expired."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from envctl.storage import load_profiles, save_profiles
from envctl.audit import log_event


class ExpireError(Exception):
    pass


def set_expiry(project: str, profile: str, expires_at: datetime) -> None:
    """Attach an expiry timestamp (UTC) to a profile."""
    store = load_profiles()
    try:
        prof = store[project][profile]
    except KeyError:
        raise ExpireError(f"Profile '{project}/{profile}' not found.")
    prof["expires_at"] = expires_at.astimezone(timezone.utc).isoformat()
    save_profiles(store)
    log_event(project, profile, "set_expiry", {"expires_at": prof["expires_at"]})


def clear_expiry(project: str, profile: str) -> None:
    """Remove expiry from a profile."""
    store = load_profiles()
    try:
        prof = store[project][profile]
    except KeyError:
        raise ExpireError(f"Profile '{project}/{profile}' not found.")
    prof.pop("expires_at", None)
    save_profiles(store)
    log_event(project, profile, "clear_expiry", {})


def get_expiry(project: str, profile: str) -> Optional[datetime]:
    """Return expiry datetime or None if not set."""
    store = load_profiles()
    try:
        prof = store[project][profile]
    except KeyError:
        raise ExpireError(f"Profile '{project}/{profile}' not found.")
    raw = prof.get("expires_at")
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def is_expired(project: str, profile: str) -> bool:
    """Return True if the profile has passed its expiry time."""
    expiry = get_expiry(project, profile)
    if expiry is None:
        return False
    return datetime.now(timezone.utc) >= expiry


def list_expired(project: str) -> list[str]:
    """Return profile names in *project* that are currently expired."""
    store = load_profiles()
    profiles = store.get(project, {})
    expired = []
    now = datetime.now(timezone.utc)
    for name, data in profiles.items():
        raw = data.get("expires_at")
        if raw and datetime.fromisoformat(raw) <= now:
            expired.append(name)
    return expired

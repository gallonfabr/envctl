"""TTL (time-to-live) support for environment profiles.

Allows setting a TTL in seconds on a profile so that it is
automatically considered stale after the given duration.
"""

from __future__ import annotations

import time
from typing import Optional

from envctl.storage import load_profiles, save_profiles


class TTLError(Exception):
    """Raised when a TTL operation fails."""


def set_ttl(project: str, profile: str, seconds: int) -> None:
    """Attach a TTL (in seconds) to *profile* under *project*."""
    if seconds <= 0:
        raise TTLError("TTL must be a positive integer number of seconds.")

    data = load_profiles()
    if project not in data or profile not in data[project]:
        raise TTLError(f"Profile '{project}/{profile}' not found.")

    meta = data[project][profile].setdefault("_meta", {})
    meta["ttl_seconds"] = seconds
    meta["ttl_set_at"] = time.time()
    save_profiles(data)


def clear_ttl(project: str, profile: str) -> None:
    """Remove the TTL from *profile* under *project*."""
    data = load_profiles()
    if project not in data or profile not in data[project]:
        raise TTLError(f"Profile '{project}/{profile}' not found.")

    meta = data[project][profile].get("_meta", {})
    meta.pop("ttl_seconds", None)
    meta.pop("ttl_set_at", None)
    if meta:
        data[project][profile]["_meta"] = meta
    else:
        data[project][profile].pop("_meta", None)
    save_profiles(data)


def get_ttl(project: str, profile: str) -> Optional[dict]:
    """Return TTL info dict or *None* if no TTL is set.

    Returned dict keys:
      - ``seconds``  – configured TTL duration
      - ``set_at``   – epoch timestamp when TTL was set
      - ``remaining`` – seconds remaining (may be negative if expired)
      - ``expired``  – bool
    """
    data = load_profiles()
    if project not in data or profile not in data[project]:
        raise TTLError(f"Profile '{project}/{profile}' not found.")

    meta = data[project][profile].get("_meta", {})
    if "ttl_seconds" not in meta:
        return None

    seconds = meta["ttl_seconds"]
    set_at = meta["ttl_set_at"]
    elapsed = time.time() - set_at
    remaining = seconds - elapsed
    return {
        "seconds": seconds,
        "set_at": set_at,
        "remaining": remaining,
        "expired": remaining <= 0,
    }


def is_expired(project: str, profile: str) -> bool:
    """Return *True* if the profile has an expired TTL."""
    info = get_ttl(project, profile)
    if info is None:
        return False
    return info["expired"]

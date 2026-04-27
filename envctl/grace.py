"""Grace period management for profiles.

A grace period allows a profile to remain usable for a set number of seconds
after it has expired, giving operators time to rotate credentials without
immediate hard failures.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from envctl.storage import load_profiles, save_profiles


class GraceError(Exception):
    """Raised when a grace-period operation fails."""


@dataclass
class GraceInfo:
    project: str
    profile: str
    seconds: int
    set_at: str  # ISO-8601


def _meta(project: str, profile: str) -> dict:
    profiles = load_profiles(project)
    if profile not in profiles:
        raise GraceError(f"Profile '{profile}' not found in project '{project}'")
    return profiles[profile].setdefault("_meta", {})


def set_grace(project: str, profile: str, seconds: int) -> GraceInfo:
    """Attach a grace period (in seconds) to *profile*."""
    if seconds <= 0:
        raise GraceError("Grace period must be a positive integer (seconds)")
    profiles = load_profiles(project)
    if profile not in profiles:
        raise GraceError(f"Profile '{profile}' not found in project '{project}'")
    now = datetime.now(timezone.utc).isoformat()
    profiles[profile].setdefault("_meta", {})["grace"] = {
        "seconds": seconds,
        "set_at": now,
    }
    save_profiles(project, profiles)
    return GraceInfo(project=project, profile=profile, seconds=seconds, set_at=now)


def clear_grace(project: str, profile: str) -> None:
    """Remove the grace period from *profile*."""
    profiles = load_profiles(project)
    if profile not in profiles:
        raise GraceError(f"Profile '{profile}' not found in project '{project}'")
    profiles[profile].get("_meta", {}).pop("grace", None)
    save_profiles(project, profiles)


def get_grace(project: str, profile: str) -> Optional[GraceInfo]:
    """Return the grace period for *profile*, or *None* if not set."""
    profiles = load_profiles(project)
    if profile not in profiles:
        raise GraceError(f"Profile '{profile}' not found in project '{project}'")
    raw = profiles[profile].get("_meta", {}).get("grace")
    if raw is None:
        return None
    return GraceInfo(
        project=project,
        profile=profile,
        seconds=raw["seconds"],
        set_at=raw["set_at"],
    )


def in_grace_period(project: str, profile: str, expired_at: datetime) -> bool:
    """Return True if *now* falls within the grace window after *expired_at*."""
    info = get_grace(project, profile)
    if info is None:
        return False
    now = datetime.now(timezone.utc)
    if expired_at.tzinfo is None:
        expired_at = expired_at.replace(tzinfo=timezone.utc)
    delta = (now - expired_at).total_seconds()
    return 0 <= delta <= info.seconds

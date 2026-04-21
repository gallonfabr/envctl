"""Badge generation for profile status summaries."""
from __future__ import annotations

from typing import Any

from envctl.storage import load_profiles
from envctl.lock import is_locked
from envctl.expire import is_expired
from envctl.pin import get_pinned


class BadgeError(Exception):
    pass


def _profile_meta(project: str, profile: str) -> dict[str, Any]:
    """Return raw profile metadata dict."""
    data = load_profiles()
    try:
        return data[project][profile]
    except KeyError:
        raise BadgeError(f"Profile '{project}/{profile}' not found")


def profile_badge(project: str, profile: str) -> dict[str, str]:
    """Return a status badge dict for a single profile.

    Keys: project, profile, locked, expired, pinned, var_count.
    """
    meta = _profile_meta(project, profile)
    vars_: dict = meta.get("vars", {})

    locked = is_locked(project, profile)
    expired = is_expired(project, profile)

    pinned_profile = get_pinned(project)
    pinned = pinned_profile == profile

    status_parts = []
    if locked:
        status_parts.append("locked")
    if expired:
        status_parts.append("expired")
    if pinned:
        status_parts.append("pinned")
    status = ",".join(status_parts) if status_parts else "ok"

    return {
        "project": project,
        "profile": profile,
        "status": status,
        "locked": str(locked).lower(),
        "expired": str(expired).lower(),
        "pinned": str(pinned).lower(),
        "var_count": str(len(vars_)),
    }


def project_badges(project: str) -> list[dict[str, str]]:
    """Return badges for all profiles in a project."""
    data = load_profiles()
    if project not in data:
        raise BadgeError(f"Project '{project}' not found")
    profiles = data[project]
    return [profile_badge(project, name) for name in profiles]


def format_badge(badge: dict[str, str]) -> str:
    """Render a badge dict as a human-readable string."""
    locked_icon = "🔒" if badge["locked"] == "true" else "🔓"
    expired_icon = "⏰" if badge["expired"] == "true" else "✅"
    pinned_icon = "📌" if badge["pinned"] == "true" else "  "
    return (
        f"{pinned_icon} {badge['project']}/{badge['profile']} "
        f"[{badge['status']}] {locked_icon} {expired_icon} "
        f"vars={badge['var_count']}"
    )

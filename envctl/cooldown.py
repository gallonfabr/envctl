"""Cooldown enforcement: prevent rapid re-application of profiles."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from envctl.storage import load_profiles, save_profiles

_META_KEY = "__cooldown__"


class CooldownError(Exception):
    """Raised when a cooldown constraint is violated or misconfigured."""


@dataclass
class CooldownInfo:
    seconds: int
    last_applied: Optional[float]

    @property
    def remaining(self) -> float:
        if self.last_applied is None:
            return 0.0
        elapsed = time.time() - self.last_applied
        return max(0.0, self.seconds - elapsed)

    @property
    def is_active(self) -> bool:
        return self.remaining > 0.0


def _meta(project: str, profile: str) -> dict:
    data = load_profiles()
    return data.get(project, {}).get(profile, {})


def set_cooldown(project: str, profile: str, seconds: int) -> None:
    """Set a cooldown period (in seconds) for a profile."""
    if seconds <= 0:
        raise CooldownError("Cooldown seconds must be a positive integer.")
    data = load_profiles()
    if project not in data or profile not in data[project]:
        raise CooldownError(f"Profile '{profile}' not found in project '{project}'.")
    data[project][profile].setdefault(_META_KEY, {})["seconds"] = seconds
    save_profiles(data)


def clear_cooldown(project: str, profile: str) -> None:
    """Remove any cooldown setting from a profile."""
    data = load_profiles()
    meta = data.get(project, {}).get(profile, {}).get(_META_KEY, {})
    meta.pop("seconds", None)
    meta.pop("last_applied", None)
    save_profiles(data)


def get_cooldown(project: str, profile: str) -> Optional[CooldownInfo]:
    """Return CooldownInfo for a profile, or None if no cooldown is set."""
    cfg = _meta(project, profile).get(_META_KEY, {})
    if "seconds" not in cfg:
        return None
    return CooldownInfo(seconds=cfg["seconds"], last_applied=cfg.get("last_applied"))


def record_apply(project: str, profile: str) -> None:
    """Record the current timestamp as the last application time."""
    data = load_profiles()
    if project not in data or profile not in data[project]:
        raise CooldownError(f"Profile '{profile}' not found in project '{project}'.")
    data[project][profile].setdefault(_META_KEY, {})["last_applied"] = time.time()
    save_profiles(data)


def assert_cooldown_clear(project: str, profile: str) -> None:
    """Raise CooldownError if the profile is still within its cooldown window."""
    info = get_cooldown(project, profile)
    if info and info.is_active:
        raise CooldownError(
            f"Profile '{profile}' is in cooldown. "
            f"{info.remaining:.1f}s remaining."
        )

"""Watermark module: attach and verify authorship metadata on profiles."""

from __future__ import annotations

import hashlib
import time
from typing import Optional

from envctl.storage import load_profiles, save_profiles


class WatermarkError(Exception):
    """Raised when a watermark operation fails."""


def _meta(profiles: dict, project: str, profile: str) -> dict:
    """Return the mutable metadata dict for a profile."""
    try:
        return profiles[project][profile]
    except KeyError:
        raise WatermarkError(f"Profile '{project}/{profile}' not found.")


def set_watermark(project: str, profile: str, author: str, note: str = "") -> dict:
    """Attach a watermark (author + timestamp + checksum) to a profile."""
    if not author.strip():
        raise WatermarkError("Author must not be empty.")

    profiles = load_profiles()
    meta = _meta(profiles, project, profile)

    timestamp = time.time()
    payload = f"{project}:{profile}:{author}:{timestamp}"
    checksum = hashlib.sha256(payload.encode()).hexdigest()[:16]

    meta["watermark"] = {
        "author": author.strip(),
        "note": note.strip(),
        "timestamp": timestamp,
        "checksum": checksum,
    }
    save_profiles(profiles)
    return meta["watermark"]


def get_watermark(project: str, profile: str) -> Optional[dict]:
    """Return the watermark dict for a profile, or None if not set."""
    profiles = load_profiles()
    meta = _meta(profiles, project, profile)
    return meta.get("watermark")


def clear_watermark(project: str, profile: str) -> None:
    """Remove the watermark from a profile."""
    profiles = load_profiles()
    meta = _meta(profiles, project, profile)
    if "watermark" not in meta:
        raise WatermarkError(f"Profile '{project}/{profile}' has no watermark.")
    del meta["watermark"]
    save_profiles(profiles)


def verify_watermark(project: str, profile: str) -> bool:
    """Verify the stored checksum matches the expected hash."""
    wm = get_watermark(project, profile)
    if wm is None:
        raise WatermarkError(f"Profile '{project}/{profile}' has no watermark.")
    payload = f"{project}:{profile}:{wm['author']}:{wm['timestamp']}"
    expected = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return wm["checksum"] == expected

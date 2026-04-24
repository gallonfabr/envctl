"""Bookmark frequently used profiles for quick access."""

from __future__ import annotations

from typing import Optional

from envctl.storage import load_profiles, save_profiles


class BookmarkError(Exception):
    pass


def _meta(project: str, profile: str, data: dict) -> dict:
    return (
        data.get(project, {})
        .get("profiles", {})
        .get(profile, {})
    )


def add_bookmark(project: str, profile: str, label: Optional[str] = None) -> None:
    """Bookmark a profile, optionally with a short label."""
    data = load_profiles()
    if project not in data or profile not in data[project].get("profiles", {}):
        raise BookmarkError(f"Profile '{profile}' not found in project '{project}'")
    meta = data[project]["profiles"][profile]
    meta["bookmarked"] = True
    if label is not None:
        meta["bookmark_label"] = label
    save_profiles(data)


def remove_bookmark(project: str, profile: str) -> None:
    """Remove a bookmark from a profile."""
    data = load_profiles()
    if project not in data or profile not in data[project].get("profiles", {}):
        raise BookmarkError(f"Profile '{profile}' not found in project '{project}'")
    meta = data[project]["profiles"][profile]
    if not meta.get("bookmarked"):
        raise BookmarkError(f"Profile '{profile}' in project '{project}' is not bookmarked")
    meta.pop("bookmarked", None)
    meta.pop("bookmark_label", None)
    save_profiles(data)


def is_bookmarked(project: str, profile: str) -> bool:
    """Return True if the profile is bookmarked."""
    data = load_profiles()
    return bool(
        _meta(project, profile, data).get("bookmarked", False)
    )


def get_bookmark_label(project: str, profile: str) -> Optional[str]:
    """Return the bookmark label for a profile, or None."""
    data = load_profiles()
    return _meta(project, profile, data).get("bookmark_label")


def list_bookmarks() -> list[dict]:
    """Return all bookmarked profiles across all projects."""
    data = load_profiles()
    results = []
    for project, proj_data in data.items():
        for profile, meta in proj_data.get("profiles", {}).items():
            if meta.get("bookmarked"):
                results.append({
                    "project": project,
                    "profile": profile,
                    "label": meta.get("bookmark_label"),
                })
    return results

"""Diff two environment profiles side by side."""

from typing import Optional
from envctl.profile import get_profile


def diff_profiles(
    project: str,
    profile_a: str,
    profile_b: str,
    password_a: Optional[str] = None,
    password_b: Optional[str] = None,
) -> dict:
    """Compare two profiles and return added, removed, changed, and unchanged keys."""
    vars_a = get_profile(project, profile_a, password=password_a)
    vars_b = get_profile(project, profile_b, password=password_b)

    if vars_a is None:
        raise ValueError(f"Profile '{profile_a}' not found in project '{project}'")
    if vars_b is None:
        raise ValueError(f"Profile '{profile_b}' not found in project '{project}'")

    keys_a = set(vars_a.keys())
    keys_b = set(vars_b.keys())

    added = {k: vars_b[k] for k in keys_b - keys_a}
    removed = {k: vars_a[k] for k in keys_a - keys_b}
    changed = {
        k: {"from": vars_a[k], "to": vars_b[k]}
        for k in keys_a & keys_b
        if vars_a[k] != vars_b[k]
    }
    unchanged = {k: vars_a[k] for k in keys_a & keys_b if vars_a[k] == vars_b[k]}

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }


def format_diff(diff: dict, show_unchanged: bool = False) -> str:
    """Format a diff dict into a human-readable string."""
    lines = []

    for key, value in diff["added"].items():
        lines.append(f"+ {key}={value}")

    for key, value in diff["removed"].items():
        lines.append(f"- {key}={value}")

    for key, meta in diff["changed"].items():
        lines.append(f"~ {key}: {meta['from']} -> {meta['to']}")

    if show_unchanged:
        for key, value in diff["unchanged"].items():
            lines.append(f"  {key}={value}")

    if not lines:
        return "No differences found."

    return "\n".join(lines)

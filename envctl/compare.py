"""Compare profiles across projects or within a project."""
from typing import Optional
from envctl.profile import get_profile
from envctl.diff import diff_profiles, format_diff
from envctl.audit import log_event


def compare_profiles(
    project_a: str,
    profile_a: str,
    project_b: str,
    profile_b: str,
    password_a: Optional[str] = None,
    password_b: Optional[str] = None,
) -> dict:
    """Return diff dict between two profiles, possibly from different projects."""
    vars_a = get_profile(project_a, profile_a, password=password_a)
    vars_b = get_profile(project_b, profile_b, password=password_b)

    result = diff_profiles(
        {"vars": vars_a},
        {"vars": vars_b},
    )

    log_event(
        project_a,
        "compare",
        {
            "profile_a": profile_a,
            "project_b": project_b,
            "profile_b": profile_b,
        },
    )
    return result


def compare_summary(diff: dict) -> str:
    """Return a human-readable summary line for a diff result."""
    added = len(diff.get("added", {}))
    removed = len(diff.get("removed", {}))
    changed = len(diff.get("changed", {}))
    return f"+{added} added  -{removed} removed  ~{changed} changed"

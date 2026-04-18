"""Lint profiles for common issues with variable names and values."""

from typing import Optional
from envctl.profile import get_profile
from envctl.storage import list_projects, list_profiles

WARN_PREFIXES = ("test_", "tmp_", "debug_", "temp_")
SUSPECT_VALUE_PATTERNS = ["", "TODO", "FIXME", "CHANGEME", "<YOUR_", "your_"]


def lint_profile(project: str, profile: str, password: Optional[str] = None) -> list[dict]:
    """Return a list of lint warnings for a given profile."""
    data = get_profile(project, profile, password=password)
    warnings = []

    for key, value in data.items():
        if not key.isupper():
            warnings.append({
                "key": key,
                "level": "warning",
                "message": f"Variable '{key}' is not uppercase.",
            })

        if any(key.lower().startswith(p) for p in WARN_PREFIXES):
            warnings.append({
                "key": key,
                "level": "warning",
                "message": f"Variable '{key}' looks temporary or test-only.",
            })

        str_val = str(value)
        if any(str_val == p or str_val.startswith(p) for p in SUSPECT_VALUE_PATTERNS):
            warnings.append({
                "key": key,
                "level": "error",
                "message": f"Variable '{key}' has a placeholder or empty value.",
            })

    return warnings


def lint_project(project: str, password: Optional[str] = None) -> dict[str, list[dict]]:
    """Lint all profiles in a project. Returns a dict of profile -> warnings."""
    results = {}
    for profile in list_profiles(project):
        try:
            results[profile] = lint_profile(project, profile, password=password)
        except Exception as exc:
            results[profile] = [{"key": None, "level": "error", "message": str(exc)}]
    return results

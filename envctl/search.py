"""Search profiles by variable key or value patterns."""

from fnmatch import fnmatch
from typing import Optional

from envctl.profile import get_profile
from envctl.storage import list_projects, list_profiles


def search_by_key(
    pattern: str,
    project: Optional[str] = None,
    password: Optional[str] = None,
) -> list[dict]:
    """Return matches [{project, profile, key, value}] where key matches pattern."""
    results = []
    projects = [project] if project else list_projects()
    for proj in projects:
        for prof_name in list_profiles(proj):
            try:
                vars_ = get_profile(proj, prof_name, password=password)
            except Exception:
                continue
            for k, v in vars_.items():
                if fnmatch(k, pattern):
                    results.append({"project": proj, "profile": prof_name, "key": k, "value": v})
    return results


def search_by_value(
    pattern: str,
    project: Optional[str] = None,
    password: Optional[str] = None,
) -> list[dict]:
    """Return matches [{project, profile, key, value}] where value matches pattern."""
    results = []
    projects = [project] if project else list_projects()
    for proj in projects:
        for prof_name in list_profiles(proj):
            try:
                vars_ = get_profile(proj, prof_name, password=password)
            except Exception:
                continue
            for k, v in vars_.items():
                if fnmatch(str(v), pattern):
                    results.append({"project": proj, "profile": prof_name, "key": k, "value": v})
    return results

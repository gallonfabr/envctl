"""Validation helpers for environment variable profiles."""

import re
from typing import Dict, List, Tuple

VAR_NAME_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')


def validate_var_name(name: str) -> bool:
    """Return True if name is a valid env var name (uppercase convention)."""
    return bool(VAR_NAME_RE.match(name))


def validate_vars(vars_dict: Dict[str, str]) -> List[Tuple[str, str]]:
    """Validate a dict of env vars.

    Returns a list of (key, reason) tuples for any invalid entries.
    """
    errors: List[Tuple[str, str]] = []
    for key, value in vars_dict.items():
        if not isinstance(key, str) or not key:
            errors.append((str(key), "key must be a non-empty string"))
        elif not validate_var_name(key):
            errors.append((key, "key must match [A-Z_][A-Z0-9_]* (uppercase)"))
        if not isinstance(value, str):
            errors.append((key, "value must be a string"))
    return errors


def validate_profile_name(name: str) -> bool:
    """Return True if profile name contains only alphanumerics, hyphens, underscores."""
    return bool(re.match(r'^[\w-]+$', name))


def validate_project_name(name: str) -> bool:
    """Return True if project name contains only alphanumerics, hyphens, underscores."""
    return bool(re.match(r'^[\w-]+$', name))


def assert_valid_profile(project: str, profile: str, vars_dict: Dict[str, str]) -> None:
    """Raise ValueError with a descriptive message if any validation fails."""
    if not validate_project_name(project):
        raise ValueError(f"Invalid project name: '{project}'")
    if not validate_profile_name(profile):
        raise ValueError(f"Invalid profile name: '{profile}'")
    errors = validate_vars(vars_dict)
    if errors:
        msg = "; ".join(f"{k}: {r}" for k, r in errors)
        raise ValueError(f"Invalid variables: {msg}")

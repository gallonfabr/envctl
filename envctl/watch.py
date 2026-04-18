"""Watch a profile and alert when environment variables drift from expected values."""

from typing import Optional
from envctl.profile import get_profile
from envctl.audit import log_event


def check_drift(project: str, profile: str, current_env: dict, password: Optional[str] = None) -> list[dict]:
    """Compare current environment against a stored profile.

    Returns a list of drift entries with keys: key, expected, actual, status.
    status is one of: 'missing', 'extra', 'changed', 'ok'
    """
    stored = get_profile(project, profile, password=password)
    stored_vars = stored.get("vars", {})

    drifts = []

    for key, expected in stored_vars.items():
        actual = current_env.get(key)
        if actual is None:
            drifts.append({"key": key, "expected": expected, "actual": None, "status": "missing"})
        elif actual != expected:
            drifts.append({"key": key, "expected": expected, "actual": actual, "status": "changed"})

    if drifts:
        log_event(project, profile, "drift_detected", detail=f"{len(drifts)} drifted key(s)")

    return drifts


def drift_summary(drifts: list[dict]) -> dict:
    """Return counts by status."""
    summary = {"missing": 0, "changed": 0}
    for d in drifts:
        status = d["status"]
        summary[status] = summary.get(status, 0) + 1
    return summary

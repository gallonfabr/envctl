"""Anomaly detection for environment variable profiles.

Detects suspicious or unusual patterns in profile variables such as
potential secrets in plain profiles, duplicate values across profiles,
unusually long values, and common misconfiguration patterns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envctl.storage import list_projects, list_profiles
from envctl.profile import get_profile

# Patterns that suggest a value might be a secret
_SECRET_KEY_HINTS = (
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "auth", "credential", "private", "access_key", "signing",
)

# Values that are almost certainly misconfigured placeholders
_PLACEHOLDER_PATTERNS = (
    "<your", "changeme", "todo", "fixme", "placeholder", "example",
    "replace_me", "insert_here",
)

_MAX_REASONABLE_LENGTH = 1024


@dataclass
class Anomaly:
    """A single detected anomaly within a profile."""

    project: str
    profile: str
    key: str
    kind: str          # e.g. 'plain_secret', 'placeholder', 'long_value', 'duplicate_value'
    detail: str
    severity: str      # 'low', 'medium', 'high'


@dataclass
class AnomalyReport:
    """Aggregated anomaly report for a project or profile."""

    project: str
    profile: str
    anomalies: List[Anomaly] = field(default_factory=list)

    @property
    def has_anomalies(self) -> bool:
        return bool(self.anomalies)

    def by_severity(self, severity: str) -> List[Anomaly]:
        return [a for a in self.anomalies if a.severity == severity]


def _check_plain_secrets(project: str, profile: str, vars_: dict) -> List[Anomaly]:
    """Flag variables whose names suggest secrets stored in a plain profile."""
    found = []
    for key, value in vars_.items():
        lower_key = key.lower()
        if any(hint in lower_key for hint in _SECRET_KEY_HINTS):
            if value and len(value) > 3:  # ignore empty / trivial values
                found.append(Anomaly(
                    project=project,
                    profile=profile,
                    key=key,
                    kind="plain_secret",
                    detail=f"Key '{key}' looks like a secret stored without encryption.",
                    severity="high",
                ))
    return found


def _check_placeholders(project: str, profile: str, vars_: dict) -> List[Anomaly]:
    """Flag variables whose values are clearly placeholder / unset."""
    found = []
    for key, value in vars_.items():
        if isinstance(value, str):
            lower_val = value.lower().strip()
            if any(lower_val.startswith(p) or lower_val == p for p in _PLACEHOLDER_PATTERNS):
                found.append(Anomaly(
                    project=project,
                    profile=profile,
                    key=key,
                    kind="placeholder",
                    detail=f"Value for '{key}' appears to be a placeholder: {value!r}",
                    severity="medium",
                ))
    return found


def _check_long_values(project: str, profile: str, vars_: dict) -> List[Anomaly]:
    """Flag variables with suspiciously long values."""
    found = []
    for key, value in vars_.items():
        if isinstance(value, str) and len(value) > _MAX_REASONABLE_LENGTH:
            found.append(Anomaly(
                project=project,
                profile=profile,
                key=key,
                kind="long_value",
                detail=(
                    f"Value for '{key}' is {len(value)} characters "
                    f"(threshold: {_MAX_REASONABLE_LENGTH})."
                ),
                severity="low",
            ))
    return found


def scan_profile(
    project: str,
    profile_name: str,
    password: Optional[str] = None,
) -> AnomalyReport:
    """Scan a single profile for anomalies and return a report."""
    report = AnomalyReport(project=project, profile=profile_name)

    try:
        vars_ = get_profile(project, profile_name, password=password)
    except Exception as exc:  # profile missing or decryption failure
        report.anomalies.append(Anomaly(
            project=project,
            profile=profile_name,
            key="",
            kind="unreadable",
            detail=f"Could not read profile: {exc}",
            severity="medium",
        ))
        return report

    # Only check for plain-secret patterns when no password was supplied
    # (encrypted profiles already protect their values).
    if password is None:
        report.anomalies.extend(_check_plain_secrets(project, profile_name, vars_))

    report.anomalies.extend(_check_placeholders(project, profile_name, vars_))
    report.anomalies.extend(_check_long_values(project, profile_name, vars_))

    return report


def scan_project(project: str, password: Optional[str] = None) -> List[AnomalyReport]:
    """Scan all profiles in a project and return one report per profile."""
    reports = []
    for profile_name in list_profiles(project):
        reports.append(scan_profile(project, profile_name, password=password))
    return reports


def scan_all(password: Optional[str] = None) -> List[AnomalyReport]:
    """Scan every profile across all known projects."""
    reports = []
    for project in list_projects():
        reports.extend(scan_project(project, password=password))
    return reports

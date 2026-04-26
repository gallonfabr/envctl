"""envctl.scorecard — aggregate profile quality scorecard.

Combines health, rating, anomaly, lint, and badge signals into a
single weighted scorecard for a profile or all profiles in a project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envctl.profile import get_profile
from envctl.storage import list_profiles
from envctl.health import check as health_check
from envctl.rating import rate_profile
from envctl.anomaly import scan as anomaly_scan
from envctl.lint import lint_profile
from envctl.audit import log_event


class ScorecardError(Exception):
    """Raised when scorecard generation fails."""


@dataclass
class ScorecardResult:
    project: str
    profile: str
    health_score: int          # 0-100
    rating_score: int          # 0-100  (grade mapped to numeric)
    anomaly_penalty: int       # 0-100  (deducted per anomaly)
    lint_penalty: int          # 0-100  (deducted per lint issue)
    total: int                 # weighted composite 0-100
    grade: str                 # A/B/C/D/F
    notes: list[str] = field(default_factory=list)


# Weights must sum to 1.0
_WEIGHTS = {
    "health": 0.40,
    "rating": 0.30,
    "anomaly": 0.20,
    "lint": 0.10,
}

_GRADE_MAP = {"A": 95, "B": 80, "C": 65, "D": 50, "F": 20}

_SCORE_GRADE = [(90, "A"), (75, "B"), (60, "C"), (45, "D")]


def _grade_from_score(score: int) -> str:
    for threshold, grade in _SCORE_GRADE:
        if score >= threshold:
            return grade
    return "F"


def _rating_to_numeric(grade: str) -> int:
    """Convert letter grade from rating module to a 0-100 numeric."""
    return _GRADE_MAP.get(grade.upper(), 20)


def scorecard(project: str, profile: str, password: Optional[str] = None) -> ScorecardResult:
    """Generate a scorecard for a single profile.

    Args:
        project:  Project name.
        profile:  Profile name.
        password: Optional decryption password for encrypted profiles.

    Returns:
        ScorecardResult with composite score and breakdown.

    Raises:
        ScorecardError: If the profile cannot be loaded or sub-checks fail.
    """
    try:
        get_profile(project, profile, password=password)
    except Exception as exc:
        raise ScorecardError(f"Cannot load profile '{profile}' in '{project}': {exc}") from exc

    notes: list[str] = []

    # --- Health (0-100) ---
    try:
        report = health_check(project, profile, password=password)
        health_score = report.score
    except Exception:
        health_score = 0
        notes.append("health check failed; score set to 0")

    # --- Rating (letter -> numeric) ---
    try:
        pr = rate_profile(project, profile, password=password)
        rating_score = _rating_to_numeric(pr.grade)
    except Exception:
        rating_score = 0
        notes.append("rating check failed; score set to 0")

    # --- Anomaly penalty (10 pts per anomaly, capped at 100) ---
    try:
        anomaly_report = anomaly_scan(project, profile, password=password)
        anomaly_count = len(anomaly_report.anomalies)
        anomaly_penalty = min(anomaly_count * 10, 100)
        if anomaly_count:
            notes.append(f"{anomaly_count} anomaly/anomalies detected")
    except Exception:
        anomaly_penalty = 0
        notes.append("anomaly scan failed; penalty skipped")

    # --- Lint penalty (5 pts per issue, capped at 100) ---
    try:
        lint_issues = lint_profile(project, profile, password=password)
        lint_count = len(lint_issues)
        lint_penalty = min(lint_count * 5, 100)
        if lint_count:
            notes.append(f"{lint_count} lint issue(s) found")
    except Exception:
        lint_penalty = 0
        notes.append("lint check failed; penalty skipped")

    # --- Composite weighted score ---
    # anomaly and lint contribute as *inverted* penalties
    composite = (
        _WEIGHTS["health"] * health_score
        + _WEIGHTS["rating"] * rating_score
        + _WEIGHTS["anomaly"] * (100 - anomaly_penalty)
        + _WEIGHTS["lint"] * (100 - lint_penalty)
    )
    total = max(0, min(100, round(composite)))
    grade = _grade_from_score(total)

    log_event(project, "scorecard", {"profile": profile, "score": total, "grade": grade})

    return ScorecardResult(
        project=project,
        profile=profile,
        health_score=health_score,
        rating_score=rating_score,
        anomaly_penalty=anomaly_penalty,
        lint_penalty=lint_penalty,
        total=total,
        grade=grade,
        notes=notes,
    )


def project_scorecard(project: str) -> list[ScorecardResult]:
    """Return scorecards for every profile in *project*, sorted by score descending."""
    profiles = list_profiles(project)
    if not profiles:
        raise ScorecardError(f"No profiles found for project '{project}'")

    results = []
    for prof in profiles:
        try:
            results.append(scorecard(project, prof))
        except ScorecardError:
            # Skip profiles that cannot be scored (e.g. encrypted without password)
            pass

    results.sort(key=lambda r: r.total, reverse=True)
    return results

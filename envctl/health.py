"""Profile health scoring — aggregates multiple checks into a single score."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envctl.profile import get_profile
from envctl.lock import is_locked
from envctl.expire import is_expired, get_expiry
from envctl.lint import lint_profile
from envctl.ttl import is_expired as ttl_expired


@dataclass
class HealthIssue:
    severity: str  # "error" | "warning" | "info"
    code: str
    message: str


@dataclass
class HealthReport:
    project: str
    profile: str
    score: int  # 0-100
    grade: str
    issues: List[HealthIssue] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return self.score >= 80


class HealthError(Exception):
    pass


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def check_profile(project: str, profile: str, password: Optional[str] = None) -> HealthReport:
    """Run all health checks and return an aggregated HealthReport."""
    try:
        get_profile(project, profile, password=password)
    except Exception as exc:
        raise HealthError(str(exc)) from exc

    issues: List[HealthIssue] = []
    deductions = 0

    # Expiry check
    try:
        if is_expired(project, profile):
            issues.append(HealthIssue("error", "EXPIRED", "Profile has passed its expiry date."))
            deductions += 30
        elif get_expiry(project, profile) is None:
            issues.append(HealthIssue("info", "NO_EXPIRY", "No expiry date set."))
            deductions += 5
    except Exception:
        pass

    # TTL check
    try:
        if ttl_expired(project, profile):
            issues.append(HealthIssue("error", "TTL_EXPIRED", "Profile TTL has elapsed."))
            deductions += 25
    except Exception:
        pass

    # Lock check (locked profiles are healthy — reward)
    try:
        if is_locked(project, profile):
            deductions -= 5  # bonus
    except Exception:
        pass

    # Lint checks
    try:
        lint_issues = lint_profile(project, profile, password=password)
        for li in lint_issues:
            severity = "warning" if li.get("level") == "warning" else "info"
            issues.append(HealthIssue(severity, "LINT", li.get("message", "Lint issue.")))
            deductions += 10
    except Exception:
        pass

    score = max(0, min(100, 100 - deductions))
    return HealthReport(
        project=project,
        profile=profile,
        score=score,
        grade=_grade(score),
        issues=issues,
    )

"""Profile quality rating based on various metadata signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envctl.storage import load_profiles
from envctl.lint import lint_profile
from envctl.lock import is_locked
from envctl.expire import is_expired
from envctl.tags import list_tags


class RatingError(Exception):
    pass


@dataclass
class ProfileRating:
    project: str
    profile: str
    score: int
    max_score: int
    breakdown: dict[str, int] = field(default_factory=dict)
    grade: str = ""

    def __post_init__(self) -> None:
        self.grade = _grade(self.score, self.max_score)


def _grade(score: int, max_score: int) -> str:
    if max_score == 0:
        return "N/A"
    pct = score / max_score
    if pct >= 0.9:
        return "A"
    if pct >= 0.75:
        return "B"
    if pct >= 0.5:
        return "C"
    if pct >= 0.25:
        return "D"
    return "F"


def rate_profile(project: str, profile: str) -> ProfileRating:
    """Compute a quality score for a profile."""
    profiles = load_profiles(project)
    if profile not in profiles:
        raise RatingError(f"Profile '{profile}' not found in project '{project}'")

    breakdown: dict[str, int] = {}
    max_score = 0

    # +30 if no lint warnings
    max_score += 30
    issues = lint_profile(project, profile)
    breakdown["lint"] = 0 if issues else 30

    # +20 if profile has at least one tag
    max_score += 20
    tags = list_tags(project, profile)
    breakdown["tagged"] = 20 if tags else 0

    # +20 if profile is locked (intentional protection)
    max_score += 20
    breakdown["locked"] = 20 if is_locked(project, profile) else 0

    # +20 if profile is not expired
    max_score += 20
    breakdown["not_expired"] = 0 if is_expired(project, profile) else 20

    # +10 if profile has at least one variable
    max_score += 10
    data = profiles[profile]
    vars_ = data.get("vars", {})
    breakdown["has_vars"] = 10 if vars_ else 0

    score = sum(breakdown.values())
    return ProfileRating(
        project=project,
        profile=profile,
        score=score,
        max_score=max_score,
        breakdown=breakdown,
    )

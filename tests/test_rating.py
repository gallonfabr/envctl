"""Tests for envctl.rating."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from envctl.rating import rate_profile, RatingError, _grade


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_PROFILES = {
    "prod": {"vars": {"DB_URL": "postgres://localhost/prod"}},
    "empty": {"vars": {}},
}


def _patch(profiles=None, lint_issues=None, locked=False, expired=False, tags=None):
    """Return a context manager that patches all external dependencies."""
    return patch.multiple(
        "envctl.rating",
        load_profiles=MagicMock(return_value=profiles or _PROFILES),
        lint_profile=MagicMock(return_value=lint_issues or []),
        is_locked=MagicMock(return_value=locked),
        is_expired=MagicMock(return_value=expired),
        list_tags=MagicMock(return_value=tags or []),
    )


# ---------------------------------------------------------------------------
# unit tests
# ---------------------------------------------------------------------------

def test_grade_a():
    assert _grade(90, 100) == "A"


def test_grade_b():
    assert _grade(75, 100) == "B"


def test_grade_f():
    assert _grade(10, 100) == "F"


def test_grade_zero_max():
    assert _grade(0, 0) == "N/A"


def test_rate_profile_missing_raises():
    with _patch(profiles={}):
        with pytest.raises(RatingError, match="not found"):
            rate_profile("myproject", "ghost")


def test_rate_profile_perfect_score():
    with _patch(lint_issues=[], locked=True, expired=False, tags=["v1"]):
        r = rate_profile("myproject", "prod")
    assert r.score == r.max_score
    assert r.grade == "A"


def test_rate_profile_no_tags_loses_points():
    with _patch(lint_issues=[], locked=True, expired=False, tags=[]):
        r = rate_profile("myproject", "prod")
    assert r.breakdown["tagged"] == 0
    assert r.score < r.max_score


def test_rate_profile_lint_issues_lose_points():
    with _patch(lint_issues=["VAR_X is lowercase"], locked=False, expired=False, tags=[]):
        r = rate_profile("myproject", "prod")
    assert r.breakdown["lint"] == 0


def test_rate_profile_expired_loses_points():
    with _patch(lint_issues=[], locked=False, expired=True, tags=[]):
        r = rate_profile("myproject", "prod")
    assert r.breakdown["not_expired"] == 0


def test_rate_profile_empty_vars_loses_points():
    with _patch(profiles=_PROFILES, lint_issues=[], locked=False, expired=False, tags=[]):
        r = rate_profile("myproject", "empty")
    assert r.breakdown["has_vars"] == 0


def test_breakdown_keys_present():
    with _patch():
        r = rate_profile("myproject", "prod")
    expected = {"lint", "tagged", "locked", "not_expired", "has_vars"}
    assert set(r.breakdown.keys()) == expected

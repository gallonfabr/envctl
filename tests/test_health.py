"""Tests for envctl.health."""
import pytest
from unittest.mock import patch, MagicMock
from envctl.health import check_profile, HealthError, HealthReport


def _patch(**kwargs):
    """Return a context manager that patches common health dependencies."""
    defaults = {
        "get_profile": MagicMock(return_value={"DB_URL": "postgres://localhost/db"}),
        "is_expired": MagicMock(return_value=False),
        "get_expiry": MagicMock(return_value="2099-01-01"),
        "ttl_expired": MagicMock(return_value=False),
        "is_locked": MagicMock(return_value=False),
        "lint_profile": MagicMock(return_value=[]),
    }
    defaults.update(kwargs)
    return [
        patch("envctl.health.get_profile", defaults["get_profile"]),
        patch("envctl.health.is_expired", defaults["is_expired"]),
        patch("envctl.health.get_expiry", defaults["get_expiry"]),
        patch("envctl.health.ttl_expired", defaults["ttl_expired"]),
        patch("envctl.health.is_locked", defaults["is_locked"]),
        patch("envctl.health.lint_profile", defaults["lint_profile"]),
    ]


def _apply(patches):
    for p in patches:
        p.start()
    return patches


def _stop(patches):
    for p in patches:
        p.stop()


def test_healthy_profile_scores_100():
    patches = _apply(_patch())
    try:
        report = check_profile("myproject", "prod")
        assert report.score == 100
        assert report.grade == "A"
        assert report.healthy is True
        assert report.issues == []
    finally:
        _stop(patches)


def test_expired_profile_deducts_score():
    patches = _apply(_patch(is_expired=MagicMock(return_value=True)))
    try:
        report = check_profile("myproject", "prod")
        assert report.score <= 70
        codes = [i.code for i in report.issues]
        assert "EXPIRED" in codes
    finally:
        _stop(patches)


def test_ttl_expired_deducts_score():
    patches = _apply(_patch(ttl_expired=MagicMock(return_value=True)))
    try:
        report = check_profile("myproject", "prod")
        assert report.score <= 75
        codes = [i.code for i in report.issues]
        assert "TTL_EXPIRED" in codes
    finally:
        _stop(patches)


def test_lint_issues_deduct_score():
    lint_issues = [{"level": "warning", "message": "lowercase key"}]
    patches = _apply(_patch(lint_profile=MagicMock(return_value=lint_issues)))
    try:
        report = check_profile("myproject", "prod")
        assert report.score <= 90
        codes = [i.code for i in report.issues]
        assert "LINT" in codes
    finally:
        _stop(patches)


def test_locked_profile_gets_bonus():
    patches = _apply(_patch(is_locked=MagicMock(return_value=True)))
    try:
        report = check_profile("myproject", "prod")
        # Locked bonus keeps score at 100 (capped)
        assert report.score == 100
    finally:
        _stop(patches)


def test_missing_profile_raises_health_error():
    with patch("envctl.health.get_profile", side_effect=KeyError("not found")):
        with pytest.raises(HealthError):
            check_profile("myproject", "ghost")


def test_no_expiry_adds_info_issue():
    patches = _apply(_patch(get_expiry=MagicMock(return_value=None)))
    try:
        report = check_profile("myproject", "prod")
        codes = [i.code for i in report.issues]
        assert "NO_EXPIRY" in codes
    finally:
        _stop(patches)


def test_grade_f_for_very_low_score():
    patches = _apply(_patch(
        is_expired=MagicMock(return_value=True),
        ttl_expired=MagicMock(return_value=True),
        lint_profile=MagicMock(return_value=[
            {"level": "warning", "message": "bad key"} for _ in range(5)
        ]),
    ))
    try:
        report = check_profile("myproject", "prod")
        assert report.grade in ("D", "F")
        assert report.healthy is False
    finally:
        _stop(patches)

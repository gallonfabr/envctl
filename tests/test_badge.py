"""Tests for envctl.badge."""
import pytest
from unittest.mock import patch, MagicMock

from envctl.badge import BadgeError, format_badge, profile_badge, project_badges


BASE_DATA = {
    "myproject": {
        "dev": {"vars": {"A": "1", "B": "2"}},
        "prod": {"vars": {"A": "prod"}},
    }
}


def _patch_all(locked=False, expired=False, pinned_profile=None):
    return [
        patch("envctl.badge.load_profiles", return_value=BASE_DATA),
        patch("envctl.badge.is_locked", return_value=locked),
        patch("envctl.badge.is_expired", return_value=expired),
        patch("envctl.badge.get_pinned", return_value=pinned_profile),
    ]


def test_profile_badge_ok():
    with patch("envctl.badge.load_profiles", return_value=BASE_DATA), \
         patch("envctl.badge.is_locked", return_value=False), \
         patch("envctl.badge.is_expired", return_value=False), \
         patch("envctl.badge.get_pinned", return_value=None):
        badge = profile_badge("myproject", "dev")
    assert badge["status"] == "ok"
    assert badge["var_count"] == "2"
    assert badge["locked"] == "false"
    assert badge["expired"] == "false"
    assert badge["pinned"] == "false"


def test_profile_badge_locked():
    with patch("envctl.badge.load_profiles", return_value=BASE_DATA), \
         patch("envctl.badge.is_locked", return_value=True), \
         patch("envctl.badge.is_expired", return_value=False), \
         patch("envctl.badge.get_pinned", return_value=None):
        badge = profile_badge("myproject", "dev")
    assert "locked" in badge["status"]
    assert badge["locked"] == "true"


def test_profile_badge_expired_and_pinned():
    with patch("envctl.badge.load_profiles", return_value=BASE_DATA), \
         patch("envctl.badge.is_locked", return_value=False), \
         patch("envctl.badge.is_expired", return_value=True), \
         patch("envctl.badge.get_pinned", return_value="dev"):
        badge = profile_badge("myproject", "dev")
    assert "expired" in badge["status"]
    assert "pinned" in badge["status"]
    assert badge["pinned"] == "true"


def test_profile_badge_missing_profile():
    with patch("envctl.badge.load_profiles", return_value=BASE_DATA):
        with pytest.raises(BadgeError, match="not found"):
            profile_badge("myproject", "staging")


def test_project_badges_returns_all():
    with patch("envctl.badge.load_profiles", return_value=BASE_DATA), \
         patch("envctl.badge.is_locked", return_value=False), \
         patch("envctl.badge.is_expired", return_value=False), \
         patch("envctl.badge.get_pinned", return_value=None):
        badges = project_badges("myproject")
    assert len(badges) == 2
    names = {b["profile"] for b in badges}
    assert names == {"dev", "prod"}


def test_project_badges_missing_project():
    with patch("envctl.badge.load_profiles", return_value=BASE_DATA):
        with pytest.raises(BadgeError, match="not found"):
            project_badges("unknown")


def test_format_badge_ok():
    badge = {
        "project": "p", "profile": "dev", "status": "ok",
        "locked": "false", "expired": "false", "pinned": "false",
        "var_count": "3",
    }
    result = format_badge(badge)
    assert "p/dev" in result
    assert "ok" in result
    assert "vars=3" in result


def test_format_badge_locked_and_pinned():
    badge = {
        "project": "p", "profile": "prod", "status": "locked,pinned",
        "locked": "true", "expired": "false", "pinned": "true",
        "var_count": "5",
    }
    result = format_badge(badge)
    assert "🔒" in result
    assert "📌" in result

"""Tests for envctl.grace."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest

from envctl.grace import (
    GraceError,
    GraceInfo,
    set_grace,
    clear_grace,
    get_grace,
    in_grace_period,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_profiles(meta: dict | None = None):
    entry = {"vars": {"KEY": "val"}}
    if meta is not None:
        entry["_meta"] = meta
    return {"prod": entry}


def _patch(profiles):
    """Return a context-manager pair that stubs load/save."""
    save = MagicMock()
    return (
        patch("envctl.grace.load_profiles", return_value=profiles),
        patch("envctl.grace.save_profiles", save),
        save,
    )


# ---------------------------------------------------------------------------
# set_grace
# ---------------------------------------------------------------------------

def test_set_grace_persists():
    profiles = _base_profiles()
    load_p = patch("envctl.grace.load_profiles", return_value=profiles)
    save_p = patch("envctl.grace.save_profiles") as _:
        pass
    with load_p, patch("envctl.grace.save_profiles") as save_mock:
        info = set_grace("myapp", "prod", 300)
    assert isinstance(info, GraceInfo)
    assert info.seconds == 300
    assert info.project == "myapp"
    assert info.profile == "prod"
    assert save_mock.called


def test_set_grace_zero_raises():
    with pytest.raises(GraceError, match="positive"):
        set_grace("myapp", "prod", 0)


def test_set_grace_negative_raises():
    with pytest.raises(GraceError, match="positive"):
        set_grace("myapp", "prod", -60)


def test_set_grace_missing_profile_raises():
    with patch("envctl.grace.load_profiles", return_value={}):
        with pytest.raises(GraceError, match="not found"):
            set_grace("myapp", "missing", 60)


# ---------------------------------------------------------------------------
# get_grace / clear_grace
# ---------------------------------------------------------------------------

def test_get_grace_returns_info():
    profiles = _base_profiles({"grace": {"seconds": 120, "set_at": "2024-01-01T00:00:00+00:00"}})
    with patch("envctl.grace.load_profiles", return_value=profiles):
        info = get_grace("myapp", "prod")
    assert info is not None
    assert info.seconds == 120


def test_get_grace_unset_returns_none():
    profiles = _base_profiles()
    with patch("envctl.grace.load_profiles", return_value=profiles):
        assert get_grace("myapp", "prod") is None


def test_get_grace_missing_profile_raises():
    with patch("envctl.grace.load_profiles", return_value={}):
        with pytest.raises(GraceError):
            get_grace("myapp", "ghost")


def test_clear_grace_removes_key():
    profiles = _base_profiles({"grace": {"seconds": 60, "set_at": "2024-01-01T00:00:00+00:00"}})
    with patch("envctl.grace.load_profiles", return_value=profiles), \
         patch("envctl.grace.save_profiles") as save_mock:
        clear_grace("myapp", "prod")
    assert "grace" not in profiles["prod"].get("_meta", {})
    assert save_mock.called


# ---------------------------------------------------------------------------
# in_grace_period
# ---------------------------------------------------------------------------

def test_in_grace_period_within_window():
    profiles = _base_profiles({"grace": {"seconds": 300, "set_at": "2024-01-01T00:00:00+00:00"}})
    expired_at = datetime.now(timezone.utc) - timedelta(seconds=100)
    with patch("envctl.grace.load_profiles", return_value=profiles):
        assert in_grace_period("myapp", "prod", expired_at) is True


def test_in_grace_period_outside_window():
    profiles = _base_profiles({"grace": {"seconds": 60, "set_at": "2024-01-01T00:00:00+00:00"}})
    expired_at = datetime.now(timezone.utc) - timedelta(seconds=200)
    with patch("envctl.grace.load_profiles", return_value=profiles):
        assert in_grace_period("myapp", "prod", expired_at) is False


def test_in_grace_period_no_grace_set():
    profiles = _base_profiles()
    expired_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    with patch("envctl.grace.load_profiles", return_value=profiles):
        assert in_grace_period("myapp", "prod", expired_at) is False

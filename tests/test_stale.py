"""Tests for envctl.stale."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from envctl.stale import StaleError, StaleProfile, find_stale, stale_summary


_PROJECTS = ["myapp"]
_PROFILES = ["dev", "staging", "prod"]

_NOW = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


def _ts(days_ago: float) -> str:
    return (_NOW - timedelta(days=days_ago)).isoformat()


@pytest.fixture()
def patch_deps():
    with (
        patch("envctl.stale.list_projects", return_value=_PROJECTS),
        patch("envctl.stale.list_profiles", return_value=_PROFILES),
        patch("envctl.stale.datetime") as mock_dt,
    ):
        mock_dt.now.return_value = _NOW
        mock_dt.fromisoformat.side_effect = datetime.fromisoformat
        yield mock_dt


def test_find_stale_missing_project():
    with patch("envctl.stale.list_projects", return_value=[]):
        with pytest.raises(StaleError, match="not found"):
            find_stale("ghost")


def test_find_stale_no_history(patch_deps):
    with patch("envctl.stale.get_history", return_value=[]):
        results = find_stale("myapp", threshold_days=30)
    assert len(results) == 3
    for r in results:
        assert r.last_applied is None
        assert r.days_idle is None


def test_find_stale_excludes_never_applied_when_flag_false(patch_deps):
    with patch("envctl.stale.get_history", return_value=[]):
        results = find_stale("myapp", threshold_days=30, include_never_applied=False)
    assert results == []


def test_find_stale_detects_idle_profiles(patch_deps):
    history_map = {
        "dev": [{"timestamp": _ts(45)}],
        "staging": [{"timestamp": _ts(10)}],
        "prod": [{"timestamp": _ts(60)}],
    }

    def _fake_history(project, profile, limit=1):
        return history_map.get(profile, [])

    with patch("envctl.stale.get_history", side_effect=_fake_history):
        results = find_stale("myapp", threshold_days=30)

    names = {r.profile for r in results}
    assert "dev" in names
    assert "prod" in names
    assert "staging" not in names


def test_find_stale_days_idle_value(patch_deps):
    history_map = {
        "dev": [{"timestamp": _ts(45)}],
        "staging": [],
        "prod": [],
    }

    def _fake_history(project, profile, limit=1):
        return history_map.get(profile, [])

    with patch("envctl.stale.get_history", side_effect=_fake_history):
        results = find_stale("myapp", threshold_days=30, include_never_applied=False)

    assert len(results) == 1
    assert results[0].profile == "dev"
    assert results[0].days_idle == 45.0


def test_stale_summary_empty():
    assert stale_summary([]) == "No stale profiles found."


def test_stale_summary_with_entries():
    entries = [
        StaleProfile("myapp", "dev", _NOW - timedelta(days=45), 45.0),
        StaleProfile("myapp", "prod", None, None),
    ]
    output = stale_summary(entries)
    assert "dev" in output
    assert "prod" in output
    assert "45.0" in output
    assert "never" in output

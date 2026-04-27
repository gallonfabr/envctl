"""Tests for envctl.quota_guard."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from envctl.quota_guard import (
    guard_add_profile,
    guard_add_vars,
    quota_status,
    QuotaGuardError,
)
from envctl.cli_quota_guard import quota_guard_cmd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch(profiles=None, list_p=None, quota=None):
    """Return a context-manager stack for common patches."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        with patch("envctl.quota_guard.get_quota", return_value=quota), \
             patch("envctl.quota_guard.list_profiles", return_value=list_p or []), \
             patch("envctl.quota_guard.load_profiles", return_value=profiles or {}):
            yield

    return _ctx()


# ---------------------------------------------------------------------------
# guard_add_profile
# ---------------------------------------------------------------------------

def test_guard_add_profile_no_quota_passes():
    with _patch(list_p=["a", "b"], quota=None):
        guard_add_profile("myproject")  # should not raise


def test_guard_add_profile_under_quota_passes():
    with _patch(list_p=["a"], quota=3):
        guard_add_profile("myproject")  # 1 used, limit 3 — fine


def test_guard_add_profile_at_quota_raises():
    with _patch(list_p=["a", "b", "c"], quota=3):
        with pytest.raises(QuotaGuardError, match="reached its profile quota"):
            guard_add_profile("myproject")


def test_guard_add_profile_over_quota_raises():
    with _patch(list_p=["a", "b", "c", "d"], quota=3):
        with pytest.raises(QuotaGuardError):
            guard_add_profile("myproject")


# ---------------------------------------------------------------------------
# guard_add_vars
# ---------------------------------------------------------------------------

def test_guard_add_vars_no_quota_passes():
    profiles = {"dev": {"vars": {"A": "1"}}}
    with _patch(profiles=profiles, quota=None):
        guard_add_vars("proj", "dev", {"B": "2"})  # should not raise


def test_guard_add_vars_within_quota_passes():
    profiles = {"dev": {"vars": {"A": "1"}}}
    with _patch(profiles=profiles, quota=5):
        guard_add_vars("proj", "dev", {"B": "2", "C": "3"})  # 3 total ≤ 5


def test_guard_add_vars_exceeds_quota_raises():
    profiles = {"dev": {"vars": {"A": "1", "B": "2", "C": "3"}}}
    with _patch(profiles=profiles, quota=4):
        with pytest.raises(QuotaGuardError, match="exceeding the quota"):
            guard_add_vars("proj", "dev", {"D": "4", "E": "5"})  # 5 > 4


def test_guard_add_vars_merge_deduplicates():
    """Overwriting an existing key should not count as a new variable."""
    profiles = {"dev": {"vars": {"A": "1", "B": "2"}}}
    with _patch(profiles=profiles, quota=2):
        guard_add_vars("proj", "dev", {"A": "updated"})  # still 2 total


# ---------------------------------------------------------------------------
# quota_status
# ---------------------------------------------------------------------------

def test_quota_status_no_quota():
    with _patch(list_p=["x", "y"], quota=None):
        result = quota_status("proj")
    assert result["quota"] is None
    assert result["used"] == 2
    assert result["available"] is None
    assert result["exceeded"] is False


def test_quota_status_with_quota():
    with _patch(list_p=["x"], quota=3):
        result = quota_status("proj")
    assert result["quota"] == 3
    assert result["used"] == 1
    assert result["available"] == 2
    assert result["exceeded"] is False


def test_quota_status_exceeded():
    with _patch(list_p=["a", "b", "c", "d"], quota=3):
        result = quota_status("proj")
    assert result["exceeded"] is True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return Runner()


class Runner:
    def __init__(self):
        self._r = CliRunner()

    def invoke(self, *args, **kwargs):
        return self._r.invoke(quota_guard_cmd, *args, **kwargs)


def test_status_unlimited(runner):
    with patch("envctl.cli_quota_guard.quota_status", return_value={
        "project": "proj", "quota": None, "used": 2, "available": None, "exceeded": False
    }):
        result = runner.invoke(["status", "proj"])
    assert result.exit_code == 0
    assert "unlimited" in result.output


def test_status_with_limit(runner):
    with patch("envctl.cli_quota_guard.quota_status", return_value={
        "project": "proj", "quota": 5, "used": 3, "available": 2, "exceeded": False
    }):
        result = runner.invoke(["status", "proj"])
    assert "5" in result.output
    assert "3" in result.output


def test_set_quota_success(runner):
    with patch("envctl.cli_quota_guard.set_quota") as mock_set:
        result = runner.invoke(["set", "proj", "10"])
    assert result.exit_code == 0
    mock_set.assert_called_once_with("proj", 10)
    assert "10" in result.output


def test_remove_quota_success(runner):
    with patch("envctl.cli_quota_guard.remove_quota") as mock_rm:
        result = runner.invoke(["remove", "proj"])
    assert result.exit_code == 0
    mock_rm.assert_called_once_with("proj")

"""Tests for envctl.trend."""
from __future__ import annotations

from unittest.mock import patch, MagicMock
import pytest

from envctl.trend import (
    TrendError,
    VarTrend,
    ProfileTrend,
    _direction,
    analyze_profile_trend,
    top_volatile_vars,
)


_PROFILE_VARS = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc"}

_EVENTS = [
    {"action": "apply", "profile": "prod", "timestamp": "2024-01-01T10:00:00", "changed_keys": ["DB_HOST", "SECRET"]},
    {"action": "apply", "profile": "prod", "timestamp": "2024-01-02T10:00:00", "changed_keys": ["SECRET"]},
    {"action": "apply", "profile": "prod", "timestamp": "2024-01-03T10:00:00", "changed_keys": []},
    {"action": "add",   "profile": "prod", "timestamp": "2024-01-04T09:00:00", "changed_keys": ["DB_HOST"]},
]


@pytest.fixture()
def patch_deps():
    with (
        patch("envctl.trend.get_profile", return_value=dict(_PROFILE_VARS)) as mock_get,
        patch("envctl.trend.read_events", return_value=list(_EVENTS)) as mock_events,
    ):
        yield mock_get, mock_events


# ---------------------------------------------------------------------------
# _direction
# ---------------------------------------------------------------------------

def test_direction_stable_no_applies():
    assert _direction(0, 0) == "stable"


def test_direction_stable_no_changes():
    assert _direction(0, 10) == "stable"


def test_direction_volatile():
    assert _direction(7, 10) == "volatile"


def test_direction_rising():
    assert _direction(4, 10) == "rising"


def test_direction_declining():
    assert _direction(1, 10) == "declining"


# ---------------------------------------------------------------------------
# analyze_profile_trend
# ---------------------------------------------------------------------------

def test_analyze_returns_profile_trend(patch_deps):
    result = analyze_profile_trend("myapp", "prod")
    assert isinstance(result, ProfileTrend)
    assert result.project == "myapp"
    assert result.profile == "prod"


def test_analyze_total_applies_counts_only_apply_events(patch_deps):
    result = analyze_profile_trend("myapp", "prod")
    # 3 apply events (the 4th is an "add" action)
    assert result.total_applies == 3


def test_analyze_var_trends_present_for_all_keys(patch_deps):
    result = analyze_profile_trend("myapp", "prod")
    keys = {vt.key for vt in result.var_trends}
    assert keys == set(_PROFILE_VARS.keys())


def test_analyze_change_counts_correct(patch_deps):
    result = analyze_profile_trend("myapp", "prod")
    by_key = {vt.key: vt for vt in result.var_trends}
    assert by_key["SECRET"].change_count == 2
    assert by_key["DB_HOST"].change_count == 1
    assert by_key["DB_PORT"].change_count == 0


def test_analyze_sorted_by_change_count_descending(patch_deps):
    result = analyze_profile_trend("myapp", "prod")
    counts = [vt.change_count for vt in result.var_trends]
    assert counts == sorted(counts, reverse=True)


def test_analyze_last_value_from_current_profile(patch_deps):
    result = analyze_profile_trend("myapp", "prod")
    by_key = {vt.key: vt for vt in result.var_trends}
    assert by_key["DB_HOST"].last_value == "localhost"


def test_analyze_raises_trend_error_on_missing_profile():
    with patch("envctl.trend.get_profile", side_effect=KeyError("not found")), \
         patch("envctl.trend.read_events", return_value=[]):
        with pytest.raises(TrendError):
            analyze_profile_trend("myapp", "ghost")


# ---------------------------------------------------------------------------
# top_volatile_vars
# ---------------------------------------------------------------------------

def test_top_volatile_vars_returns_n(patch_deps):
    result = top_volatile_vars("myapp", "prod", n=2)
    assert len(result) == 2


def test_top_volatile_vars_most_changed_first(patch_deps):
    result = top_volatile_vars("myapp", "prod", n=1)
    assert result[0].key == "SECRET"

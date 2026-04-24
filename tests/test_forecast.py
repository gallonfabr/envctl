"""Tests for envctl.forecast."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from envctl.forecast import ForecastError, forecast_project, top_profiles, _trend


def _entry(days_ago: float) -> dict:
    ts = (datetime.utcnow() - timedelta(days=days_ago)).isoformat()
    return {"applied_at": ts, "profile": "p"}


@pytest.fixture()
def patch_deps():
    """Patch storage and history dependencies."""
    with patch("envctl.forecast.list_profiles") as mock_lp, \
         patch("envctl.forecast.list_projects") as mock_lproj, \
         patch("envctl.forecast.get_history") as mock_gh:
        yield mock_lproj, mock_lp, mock_gh


def test_trend_rising():
    assert _trend(6, 8) == "rising"  # 6 >= 2*1.5=3 → rising


def test_trend_declining():
    assert _trend(0, 8) == "declining"


def test_trend_stable():
    assert _trend(2, 8) == "stable"


def test_trend_inactive():
    assert _trend(0, 0) == "inactive"


def test_forecast_project_no_profiles(patch_deps):
    _, mock_lp, _ = patch_deps
    mock_lp.return_value = []
    with pytest.raises(ForecastError, match="No profiles found"):
        forecast_project("myproject")


def test_forecast_project_returns_usage(patch_deps):
    _, mock_lp, mock_gh = patch_deps
    mock_lp.return_value = ["dev", "prod"]
    mock_gh.side_effect = lambda proj, prof: [
        _entry(1), _entry(3), _entry(10), _entry(40)
    ] if prof == "dev" else [_entry(2)]

    results = forecast_project("myproject")
    assert len(results) == 2
    dev = next(r for r in results if r.profile == "dev")
    assert dev.total_applies == 4
    assert dev.applies_last_7d == 2
    assert dev.applies_last_30d == 3
    assert dev.last_applied is not None


def test_forecast_project_sorted_by_30d(patch_deps):
    _, mock_lp, mock_gh = patch_deps
    mock_lp.return_value = ["dev", "prod"]
    mock_gh.side_effect = lambda proj, prof: (
        [_entry(1)] if prof == "dev" else [_entry(2), _entry(3), _entry(4)]
    )
    results = forecast_project("myproject")
    assert results[0].profile == "prod"


def test_forecast_project_empty_history(patch_deps):
    _, mock_lp, mock_gh = patch_deps
    mock_lp.return_value = ["staging"]
    mock_gh.return_value = []
    results = forecast_project("myproject")
    assert results[0].trend == "inactive"
    assert results[0].last_applied is None


def test_top_profiles_returns_n(patch_deps):
    mock_lproj, mock_lp, mock_gh = patch_deps
    mock_lproj.return_value = ["proj1", "proj2"]
    mock_lp.return_value = ["dev"]
    mock_gh.return_value = [_entry(1), _entry(2)]
    results = top_profiles(n=3)
    assert len(results) <= 3


def test_top_profiles_skips_empty_projects(patch_deps):
    mock_lproj, mock_lp, mock_gh = patch_deps
    mock_lproj.return_value = ["empty_proj", "real_proj"]
    mock_lp.side_effect = lambda proj: [] if proj == "empty_proj" else ["dev"]
    mock_gh.return_value = [_entry(1)]
    results = top_profiles(n=5)
    assert all(r.project == "real_proj" for r in results)

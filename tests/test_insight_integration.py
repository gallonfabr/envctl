"""Integration tests for profile/project insight using real storage fixtures."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from envctl.insight import profile_insight, project_insight, InsightError


BASE_STORE = {
    "alpha": {
        "staging": {"vars": {"HOST": "localhost", "PORT": "8080"}, "tags": ["staging"]},
        "production": {"vars": {"HOST": "prod.example.com"}, "tags": []},
    }
}


@pytest.fixture()
 def isolated():
    """Patch all external dependencies with deterministic values."""
    with (
        patch("envctl.insight.load_profiles", return_value=BASE_STORE),
        patch("envctl.insight.list_profiles", side_effect=lambda p: list(BASE_STORE.get(p, {}).keys()) if p in BASE_STORE else None),
        patch("envctl.insight.is_locked", return_value=False),
        patch("envctl.insight.is_expired", return_value=False),
        patch("envctl.insight.get_pinned", return_value="staging"),
        patch("envctl.insight.get_expiry", return_value=None),
        patch("envctl.insight.search_events", return_value=[
            {"event": "apply", "profile": "staging"},
            {"event": "apply", "profile": "staging"},
            {"event": "apply", "profile": "production"},
        ]),
    ):
        yield


def test_full_profile_insight(isolated):
    ins = profile_insight("alpha", "staging")
    assert ins.var_count == 2
    assert ins.is_pinned is True
    assert ins.recent_applies == 2
    assert "staging" in ins.tags


def test_full_project_insight(isolated):
    ins = project_insight("alpha")
    assert ins.profile_count == 2
    assert ins.total_vars == 3
    assert ins.pinned_profile == "staging"
    names = [p.profile for p in ins.profiles]
    assert "staging" in names
    assert "production" in names


def test_missing_project_raises(isolated):
    with pytest.raises(InsightError):
        project_insight("does_not_exist")


def test_missing_profile_raises(isolated):
    with pytest.raises(InsightError):
        profile_insight("alpha", "nope")

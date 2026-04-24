"""Tests for envctl.insight."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from envctl.insight import InsightError, profile_insight, project_insight


STORE = {
    "myproject": {
        "dev": {"vars": {"A": "1", "B": "2"}, "tags": ["local"]},
        "prod": {"vars": {"A": "x"}, "tags": []},
    }
}


def _patch(store=None, locked=False, expired=False, pinned=None, expiry=None, events=None):
    store = store or STORE
    events = events or []
    return [
        patch("envctl.insight.load_profiles", return_value=store),
        patch("envctl.insight.list_profiles", return_value=list(store.get("myproject", {}).keys())),
        patch("envctl.insight.is_locked", return_value=locked),
        patch("envctl.insight.is_expired", return_value=expired),
        patch("envctl.insight.get_pinned", return_value=pinned),
        patch("envctl.insight.get_expiry", return_value=expiry),
        patch("envctl.insight.search_events", return_value=events),
    ]


def test_profile_insight_basic():
    with _patch()[0], _patch()[1], _patch()[2], _patch()[3], _patch()[4], _patch()[5], _patch()[6]:
        # Use context managers properly
        pass

    patches = _patch()
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        ins = profile_insight("myproject", "dev")
    assert ins.var_count == 2
    assert ins.tags == ["local"]
    assert ins.is_locked is False
    assert ins.is_expired is False


def test_profile_insight_locked_and_expired():
    patches = _patch(locked=True, expired=True, pinned="dev")
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        ins = profile_insight("myproject", "dev")
    assert ins.is_locked is True
    assert ins.is_expired is True
    assert ins.is_pinned is True


def test_profile_insight_missing_profile():
    patches = _patch()
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        with pytest.raises(InsightError, match="not found"):
            profile_insight("myproject", "nonexistent")


def test_profile_insight_recent_applies():
    events = [
        {"event": "apply", "profile": "dev"},
        {"event": "apply", "profile": "dev"},
        {"event": "apply", "profile": "prod"},
        {"event": "add", "profile": "dev"},
    ]
    patches = _patch(events=events)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        ins = profile_insight("myproject", "dev")
    assert ins.recent_applies == 2


def test_project_insight_aggregates():
    patches = _patch()
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        ins = project_insight("myproject")
    assert ins.profile_count == 2
    assert ins.total_vars == 3  # 2 + 1
    assert len(ins.profiles) == 2


def test_project_insight_missing_project():
    with patch("envctl.insight.list_profiles", return_value=None):
        with pytest.raises(InsightError, match="not found"):
            project_insight("ghost")


def test_project_insight_counts_locked_expired():
    patches = _patch(locked=True, expired=True)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        ins = project_insight("myproject")
    assert ins.locked_count == 2
    assert ins.expired_count == 2

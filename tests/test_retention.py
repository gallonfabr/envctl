"""Tests for envctl.retention."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest

from envctl.retention import (
    RetentionError,
    set_retention,
    get_retention,
    clear_retention,
    apply_retention,
)


_BASE_PROFILES: dict = {
    "myproject": {
        "dev": {"vars": {"A": "1"}},
        "prod": {"vars": {"A": "2"}},
    }
}


@pytest.fixture()
def patch_storage():
    store: dict = {}

    def _load():
        import copy
        return copy.deepcopy(store)

    def _save(data):
        store.clear()
        store.update(data)

    store.update(__import__("copy").deepcopy(_BASE_PROFILES))

    with patch("envctl.retention.load_profiles", side_effect=_load), \
         patch("envctl.retention.save_profiles", side_effect=_save), \
         patch("envctl.retention.log_event"):
        yield store


def test_set_retention_persists(patch_storage):
    set_retention("myproject", 30)
    assert get_retention("myproject") == 30


def test_set_retention_zero_raises(patch_storage):
    with pytest.raises(RetentionError):
        set_retention("myproject", 0)


def test_set_retention_negative_raises(patch_storage):
    with pytest.raises(RetentionError):
        set_retention("myproject", -5)


def test_get_retention_not_set_returns_none(patch_storage):
    assert get_retention("myproject") is None


def test_clear_retention_removes_policy(patch_storage):
    set_retention("myproject", 10)
    clear_retention("myproject")
    assert get_retention("myproject") is None


def _make_history_entry(days_ago: float):
    ts = (datetime.now(tz=timezone.utc) - timedelta(days=days_ago)).isoformat()
    return [{"applied_at": ts, "profile": "dev"}]


def test_apply_retention_purges_stale(patch_storage):
    set_retention("myproject", 7)
    with patch("envctl.retention.get_history") as mock_hist:
        mock_hist.side_effect = lambda proj, prof, limit: _make_history_entry(10)
        purged = apply_retention("myproject")
    assert "dev" in purged
    assert "prod" in purged


def test_apply_retention_keeps_recent(patch_storage):
    set_retention("myproject", 7)
    with patch("envctl.retention.get_history") as mock_hist:
        mock_hist.side_effect = lambda proj, prof, limit: _make_history_entry(2)
        purged = apply_retention("myproject")
    assert purged == []


def test_apply_retention_dry_run_does_not_delete(patch_storage):
    set_retention("myproject", 7)
    with patch("envctl.retention.get_history") as mock_hist:
        mock_hist.side_effect = lambda proj, prof, limit: _make_history_entry(20)
        purged = apply_retention("myproject", dry_run=True)
    assert len(purged) == 2
    # profiles should still exist
    assert "dev" in patch_storage["myproject"]
    assert "prod" in patch_storage["myproject"]


def test_apply_retention_no_policy_raises(patch_storage):
    with pytest.raises(RetentionError, match="No retention policy"):
        apply_retention("myproject")


def test_apply_retention_purges_never_applied(patch_storage):
    set_retention("myproject", 7)
    with patch("envctl.retention.get_history", return_value=[]):
        purged = apply_retention("myproject")
    assert "dev" in purged

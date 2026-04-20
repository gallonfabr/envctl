"""Tests for envctl.quota."""

import pytest
from unittest.mock import patch, MagicMock

from envctl.quota import (
    set_quota,
    remove_quota,
    get_quota,
    check_quota,
    quota_status,
    QuotaError,
    QUOTA_KEY,
)


@pytest.fixture(autouse=True)
def reset_profiles():
    store = {}

    def _load():
        return store

    def _save(data):
        store.clear()
        store.update(data)

    def _list_profiles(project):
        return list(store.get(project, {}).keys())

    with patch("envctl.quota.load_profiles", side_effect=_load), \
         patch("envctl.quota.save_profiles", side_effect=_save), \
         patch("envctl.quota.list_profiles", side_effect=_list_profiles):
        yield store


def test_set_quota_persists(reset_profiles):
    set_quota("myproject", 5)
    assert reset_profiles["myproject"][QUOTA_KEY] == 5


def test_set_quota_invalid_limit_raises(reset_profiles):
    with pytest.raises(QuotaError, match="positive integer"):
        set_quota("myproject", 0)


def test_set_quota_negative_raises(reset_profiles):
    with pytest.raises(QuotaError):
        set_quota("myproject", -3)


def test_get_quota_returns_limit(reset_profiles):
    reset_profiles["myproject"] = {QUOTA_KEY: 3}
    assert get_quota("myproject") == 3


def test_get_quota_returns_none_when_unset(reset_profiles):
    reset_profiles["myproject"] = {"dev": {}}
    assert get_quota("myproject") is None


def test_get_quota_missing_project_returns_none(reset_profiles):
    assert get_quota("ghost") is None


def test_remove_quota(reset_profiles):
    reset_profiles["myproject"] = {QUOTA_KEY: 10, "dev": {}}
    remove_quota("myproject")
    assert QUOTA_KEY not in reset_profiles.get("myproject", {})


def test_remove_quota_noop_when_not_set(reset_profiles):
    reset_profiles["myproject"] = {"dev": {}}
    remove_quota("myproject")  # should not raise


def test_check_quota_passes_when_under_limit(reset_profiles):
    reset_profiles["myproject"] = {QUOTA_KEY: 3, "dev": {}, "staging": {}}
    check_quota("myproject")  # 2 profiles < 3 limit — should not raise


def test_check_quota_raises_when_at_limit(reset_profiles):
    reset_profiles["myproject"] = {
        QUOTA_KEY: 2, "dev": {}, "staging": {}
    }
    with pytest.raises(QuotaError, match="quota of 2"):
        check_quota("myproject")


def test_check_quota_unlimited_never_raises(reset_profiles):
    reset_profiles["myproject"] = {f"p{i}": {} for i in range(100)}
    check_quota("myproject")  # no quota set — must not raise


def test_quota_status_with_limit(reset_profiles):
    reset_profiles["myproject"] = {QUOTA_KEY: 5, "dev": {}, "prod": {}}
    status = quota_status("myproject")
    assert status["limit"] == 5
    assert status["used"] == 2
    assert status["available"] == 3


def test_quota_status_unlimited(reset_profiles):
    reset_profiles["myproject"] = {"dev": {}}
    status = quota_status("myproject")
    assert status["limit"] is None
    assert status["available"] is None
    assert status["used"] == 1

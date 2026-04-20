"""Tests for envctl.access."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from envctl.access import (
    AccessError,
    assert_access,
    clear_allowed_users,
    get_allowed_users,
    list_restricted_profiles,
    set_allowed_users,
)


BASE_PROFILES = {
    "myapp": {
        "dev": {"vars": {"KEY": "val"}},
        "prod": {"vars": {"KEY": "prodval"}, "allowed_users": ["alice"]},
    }
}


@pytest.fixture()
def patch_storage():
    """Patch load/save so tests don't touch disk."""
    import copy

    store = copy.deepcopy(BASE_PROFILES)

    with patch("envctl.access.load_profiles", return_value=store), \
         patch("envctl.access.save_profiles") as mock_save:
        yield store, mock_save


def test_set_allowed_users_persists(patch_storage):
    store, mock_save = patch_storage
    set_allowed_users("myapp", "dev", ["alice", "bob"])
    assert store["myapp"]["dev"]["allowed_users"] == ["alice", "bob"]
    mock_save.assert_called_once()


def test_set_allowed_users_missing_profile(patch_storage):
    with pytest.raises(AccessError, match="not found"):
        set_allowed_users("myapp", "staging", ["alice"])


def test_get_allowed_users_returns_list(patch_storage):
    result = get_allowed_users("myapp", "prod")
    assert result == ["alice"]


def test_get_allowed_users_unrestricted(patch_storage):
    result = get_allowed_users("myapp", "dev")
    assert result is None


def test_clear_allowed_users_removes_key(patch_storage):
    store, mock_save = patch_storage
    clear_allowed_users("myapp", "prod")
    assert "allowed_users" not in store["myapp"]["prod"]
    mock_save.assert_called_once()


def test_clear_allowed_users_missing_profile(patch_storage):
    with pytest.raises(AccessError, match="not found"):
        clear_allowed_users("myapp", "ghost")


def test_assert_access_unrestricted_passes(patch_storage):
    # dev has no allowed_users — any user should pass
    assert_access("myapp", "dev", user="anyone")


def test_assert_access_allowed_user_passes(patch_storage):
    assert_access("myapp", "prod", user="alice")


def test_assert_access_denied_raises(patch_storage):
    with pytest.raises(AccessError, match="not allowed"):
        assert_access("myapp", "prod", user="mallory")


def test_assert_access_uses_env_user(patch_storage, monkeypatch):
    monkeypatch.setenv("USER", "alice")
    assert_access("myapp", "prod")  # no explicit user arg


def test_list_restricted_profiles(patch_storage):
    result = list_restricted_profiles("myapp")
    assert result == ["prod"]


def test_list_restricted_profiles_unknown_project(patch_storage):
    result = list_restricted_profiles("unknown")
    assert result == []

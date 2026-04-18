"""Tests for envctl.lock."""

import pytest
from unittest.mock import patch
from envctl.lock import lock_profile, unlock_profile, is_locked, assert_unlocked, LockError

BASE_DATA = {
    "myproject": {
        "dev": {"vars": {"FOO": "bar"}},
        "prod": {"vars": {"FOO": "baz"}, "_locked": True},
    }
}


def _copy():
    import copy
    return copy.deepcopy(BASE_DATA)


@pytest.fixture(autouse=True)
def patch_storage(tmp_path):
    store = _copy()
    with patch("envctl.lock.load_profiles", side_effect=lambda: _copy() if not store.get("__dirty") else store), \
         patch("envctl.lock.save_profiles", side_effect=lambda d: store.update(d) or store.update({"__dirty": True})):
        yield store


def test_lock_profile_sets_flag(patch_storage):
    lock_profile("myproject", "dev")
    assert patch_storage["myproject"]["dev"]["_locked"] is True


def test_lock_missing_profile_raises():
    with patch("envctl.lock.load_profiles", return_value=_copy()):
        with pytest.raises(LockError, match="not found"):
            lock_profile("myproject", "staging")


def test_unlock_profile_removes_flag(patch_storage):
    unlock_profile("myproject", "prod")
    assert "_locked" not in patch_storage["myproject"]["prod"]


def test_unlock_missing_profile_raises():
    with patch("envctl.lock.load_profiles", return_value=_copy()):
        with pytest.raises(LockError):
            unlock_profile("ghost", "dev")


def test_is_locked_true():
    with patch("envctl.lock.load_profiles", return_value=_copy()):
        assert is_locked("myproject", "prod") is True


def test_is_locked_false():
    with patch("envctl.lock.load_profiles", return_value=_copy()):
        assert is_locked("myproject", "dev") is False


def test_is_locked_missing_returns_false():
    with patch("envctl.lock.load_profiles", return_value=_copy()):
        assert is_locked("ghost", "dev") is False


def test_assert_unlocked_passes_for_unlocked():
    with patch("envctl.lock.load_profiles", return_value=_copy()):
        assert_unlocked("myproject", "dev")  # should not raise


def test_assert_unlocked_raises_for_locked():
    with patch("envctl.lock.load_profiles", return_value=_copy()):
        with pytest.raises(LockError, match="locked"):
            assert_unlocked("myproject", "prod")

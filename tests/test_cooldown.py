"""Tests for envctl.cooldown."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from envctl.cooldown import (
    CooldownError,
    CooldownInfo,
    assert_cooldown_clear,
    clear_cooldown,
    get_cooldown,
    record_apply,
    set_cooldown,
)
from envctl.storage import load_profiles, save_profiles


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store = tmp_path / "profiles.json"
    monkeypatch.setattr("envctl.storage.get_store_path", lambda: store)
    data = {"myproject": {"dev": {"vars": {"FOO": "bar"}}}}
    save_profiles(data)
    yield


def test_set_cooldown_persists():
    set_cooldown("myproject", "dev", 60)
    info = get_cooldown("myproject", "dev")
    assert info is not None
    assert info.seconds == 60


def test_set_cooldown_zero_raises():
    with pytest.raises(CooldownError, match="positive integer"):
        set_cooldown("myproject", "dev", 0)


def test_set_cooldown_negative_raises():
    with pytest.raises(CooldownError, match="positive integer"):
        set_cooldown("myproject", "dev", -5)


def test_set_cooldown_missing_profile_raises():
    with pytest.raises(CooldownError, match="not found"):
        set_cooldown("myproject", "ghost", 30)


def test_get_cooldown_returns_none_when_unset():
    assert get_cooldown("myproject", "dev") is None


def test_clear_cooldown_removes_setting():
    set_cooldown("myproject", "dev", 60)
    record_apply("myproject", "dev")
    clear_cooldown("myproject", "dev")
    assert get_cooldown("myproject", "dev") is None


def test_record_apply_sets_timestamp():
    set_cooldown("myproject", "dev", 60)
    before = time.time()
    record_apply("myproject", "dev")
    info = get_cooldown("myproject", "dev")
    assert info.last_applied is not None
    assert info.last_applied >= before


def test_record_apply_missing_profile_raises():
    with pytest.raises(CooldownError, match="not found"):
        record_apply("myproject", "ghost")


def test_cooldown_info_remaining_no_last_applied():
    info = CooldownInfo(seconds=30, last_applied=None)
    assert info.remaining == 0.0
    assert not info.is_active


def test_cooldown_info_active_when_recent():
    info = CooldownInfo(seconds=120, last_applied=time.time())
    assert info.is_active
    assert info.remaining > 0.0


def test_cooldown_info_inactive_when_expired():
    info = CooldownInfo(seconds=1, last_applied=time.time() - 10)
    assert not info.is_active
    assert info.remaining == 0.0


def test_assert_cooldown_clear_raises_when_active():
    set_cooldown("myproject", "dev", 300)
    record_apply("myproject", "dev")
    with pytest.raises(CooldownError, match="in cooldown"):
        assert_cooldown_clear("myproject", "dev")


def test_assert_cooldown_clear_passes_when_no_cooldown():
    assert_cooldown_clear("myproject", "dev")  # no exception


def test_assert_cooldown_clear_passes_after_window():
    set_cooldown("myproject", "dev", 1)
    record_apply("myproject", "dev")
    time.sleep(1.1)
    assert_cooldown_clear("myproject", "dev")  # no exception

"""Tests for envctl.expire module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from envctl.expire import (
    ExpireError,
    clear_expiry,
    get_expiry,
    is_expired,
    list_expired,
    set_expiry,
)
from envctl.storage import load_profiles, save_profiles


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store_file = tmp_path / "profiles.json"
    monkeypatch.setattr("envctl.storage.get_store_path", lambda: store_file)
    monkeypatch.setattr("envctl.audit.get_audit_path", lambda: tmp_path / "audit.jsonl")
    # seed a profile
    save_profiles({"myapp": {"dev": {"vars": {"FOO": "bar"}}}})
    yield


def _future(days=1):
    return datetime.now(timezone.utc) + timedelta(days=days)


def _past(days=1):
    return datetime.now(timezone.utc) - timedelta(days=days)


def test_set_expiry_persists():
    expiry = _future()
    set_expiry("myapp", "dev", expiry)
    stored = get_expiry("myapp", "dev")
    assert stored is not None
    assert abs((stored - expiry).total_seconds()) < 1


def test_set_expiry_missing_profile():
    with pytest.raises(ExpireError):
        set_expiry("myapp", "ghost", _future())


def test_clear_expiry_removes_field():
    set_expiry("myapp", "dev", _future())
    clear_expiry("myapp", "dev")
    assert get_expiry("myapp", "dev") is None


def test_clear_expiry_idempotent():
    clear_expiry("myapp", "dev")  # no expiry set — should not raise


def test_clear_expiry_missing_profile():
    with pytest.raises(ExpireError):
        clear_expiry("myapp", "ghost")


def test_is_expired_future():
    set_expiry("myapp", "dev", _future())
    assert is_expired("myapp", "dev") is False


def test_is_expired_past():
    set_expiry("myapp", "dev", _past())
    assert is_expired("myapp", "dev") is True


def test_is_expired_no_expiry():
    assert is_expired("myapp", "dev") is False


def test_list_expired_returns_only_past():
    store = load_profiles()
    store["myapp"]["prod"] = {"vars": {}, "expires_at": _future().isoformat()}
    store["myapp"]["staging"] = {"vars": {}, "expires_at": _past().isoformat()}
    save_profiles(store)

    expired = list_expired("myapp")
    assert "staging" in expired
    assert "prod" not in expired
    assert "dev" not in expired

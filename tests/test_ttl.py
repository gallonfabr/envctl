"""Tests for envctl.ttl."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from envctl import ttl as ttl_mod
from envctl.storage import load_profiles, save_profiles


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    """Redirect storage to a temp file and pre-seed one profile."""
    store = tmp_path / "profiles.json"
    monkeypatch.setattr("envctl.storage.get_store_path", lambda: store)

    data = {"myproject": {"dev": {"vars": {"FOO": "bar"}}}}
    save_profiles(data)
    yield


# ---------------------------------------------------------------------------
# set_ttl
# ---------------------------------------------------------------------------

def test_set_ttl_persists():
    ttl_mod.set_ttl("myproject", "dev", 300)
    data = load_profiles()
    meta = data["myproject"]["dev"]["_meta"]
    assert meta["ttl_seconds"] == 300
    assert "ttl_set_at" in meta


def test_set_ttl_zero_raises():
    with pytest.raises(ttl_mod.TTLError, match="positive"):
        ttl_mod.set_ttl("myproject", "dev", 0)


def test_set_ttl_negative_raises():
    with pytest.raises(ttl_mod.TTLError, match="positive"):
        ttl_mod.set_ttl("myproject", "dev", -10)


def test_set_ttl_missing_profile_raises():
    with pytest.raises(ttl_mod.TTLError, match="not found"):
        ttl_mod.set_ttl("myproject", "ghost", 60)


def test_set_ttl_missing_project_raises():
    with pytest.raises(ttl_mod.TTLError, match="not found"):
        ttl_mod.set_ttl("ghost", "dev", 60)


# ---------------------------------------------------------------------------
# clear_ttl
# ---------------------------------------------------------------------------

def test_clear_ttl_removes_meta():
    ttl_mod.set_ttl("myproject", "dev", 300)
    ttl_mod.clear_ttl("myproject", "dev")
    data = load_profiles()
    assert "_meta" not in data["myproject"]["dev"]


def test_clear_ttl_missing_profile_raises():
    with pytest.raises(ttl_mod.TTLError, match="not found"):
        ttl_mod.clear_ttl("myproject", "ghost")


# ---------------------------------------------------------------------------
# get_ttl
# ---------------------------------------------------------------------------

def test_get_ttl_returns_none_when_not_set():
    assert ttl_mod.get_ttl("myproject", "dev") is None


def test_get_ttl_returns_info():
    ttl_mod.set_ttl("myproject", "dev", 120)
    info = ttl_mod.get_ttl("myproject", "dev")
    assert info is not None
    assert info["seconds"] == 120
    assert info["remaining"] > 0
    assert info["expired"] is False


def test_get_ttl_expired():
    with patch("envctl.ttl.time") as mock_time:
        mock_time.time.return_value = 1_000_000.0
        ttl_mod.set_ttl("myproject", "dev", 60)

        mock_time.time.return_value = 1_000_000.0 + 61
        info = ttl_mod.get_ttl("myproject", "dev")

    assert info["expired"] is True
    assert info["remaining"] < 0


# ---------------------------------------------------------------------------
# is_expired
# ---------------------------------------------------------------------------

def test_is_expired_false_when_no_ttl():
    assert ttl_mod.is_expired("myproject", "dev") is False


def test_is_expired_false_within_ttl():
    ttl_mod.set_ttl("myproject", "dev", 9999)
    assert ttl_mod.is_expired("myproject", "dev") is False


def test_is_expired_true_after_ttl():
    with patch("envctl.ttl.time") as mock_time:
        mock_time.time.return_value = 2_000_000.0
        ttl_mod.set_ttl("myproject", "dev", 30)

        mock_time.time.return_value = 2_000_000.0 + 31
        result = ttl_mod.is_expired("myproject", "dev")

    assert result is True

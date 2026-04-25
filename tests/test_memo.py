"""Tests for envctl.memo."""

from __future__ import annotations

import pytest

from envctl.memo import MemoError, clear_memo, get_memo, list_memos, set_memo
from envctl.storage import load_profiles, save_profiles


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store = tmp_path / "profiles.json"
    monkeypatch.setenv("ENVCTL_STORE", str(store))
    # Seed with two profiles in one project
    data = {
        "projects": {
            "myapp": {
                "dev": {"vars": {"FOO": "bar"}},
                "prod": {"vars": {"FOO": "baz"}},
            }
        }
    }
    save_profiles(data)
    yield


def test_set_memo_persists():
    set_memo("myapp", "dev", "development profile")
    memo = get_memo("myapp", "dev")
    assert memo is not None
    assert memo["text"] == "development profile"
    assert "updated_at" in memo


def test_set_memo_overwrites():
    set_memo("myapp", "dev", "first note")
    set_memo("myapp", "dev", "second note")
    memo = get_memo("myapp", "dev")
    assert memo["text"] == "second note"


def test_set_memo_strips_whitespace():
    set_memo("myapp", "dev", "  padded  ")
    memo = get_memo("myapp", "dev")
    assert memo["text"] == "padded"


def test_set_memo_empty_raises():
    with pytest.raises(MemoError, match="empty"):
        set_memo("myapp", "dev", "   ")


def test_set_memo_missing_profile_raises():
    with pytest.raises(MemoError, match="not found"):
        set_memo("myapp", "ghost", "hello")


def test_get_memo_returns_none_when_not_set():
    result = get_memo("myapp", "dev")
    assert result is None


def test_get_memo_missing_profile_raises():
    with pytest.raises(MemoError):
        get_memo("myapp", "nonexistent")


def test_clear_memo_removes_note():
    set_memo("myapp", "dev", "temporary note")
    clear_memo("myapp", "dev")
    assert get_memo("myapp", "dev") is None


def test_clear_memo_noop_when_not_set():
    # Should not raise even if no memo exists
    clear_memo("myapp", "dev")
    assert get_memo("myapp", "dev") is None


def test_list_memos_returns_profiles_with_memos():
    set_memo("myapp", "dev", "dev note")
    results = list_memos("myapp")
    assert len(results) == 1
    assert results[0]["profile"] == "dev"
    assert results[0]["text"] == "dev note"


def test_list_memos_empty_when_none_set():
    results = list_memos("myapp")
    assert results == []


def test_list_memos_missing_project_raises():
    with pytest.raises(MemoError, match="not found"):
        list_memos("unknown_project")

"""Tests for envctl.bookmark."""

from __future__ import annotations

import pytest

from envctl.bookmark import (
    BookmarkError,
    add_bookmark,
    get_bookmark_label,
    is_bookmarked,
    list_bookmarks,
    remove_bookmark,
)
from envctl.storage import load_profiles, save_profiles


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store = tmp_path / "profiles.json"
    monkeypatch.setattr("envctl.storage.get_store_path", lambda: store)
    data = {
        "myproject": {
            "profiles": {
                "dev": {"vars": {"KEY": "val"}},
                "prod": {"vars": {"KEY": "prod_val"}},
            }
        }
    }
    save_profiles(data)
    yield


def test_add_bookmark_sets_flag():
    add_bookmark("myproject", "dev")
    assert is_bookmarked("myproject", "dev") is True


def test_add_bookmark_with_label():
    add_bookmark("myproject", "dev", label="main dev env")
    assert get_bookmark_label("myproject", "dev") == "main dev env"


def test_add_bookmark_missing_profile_raises():
    with pytest.raises(BookmarkError, match="not found"):
        add_bookmark("myproject", "staging")


def test_add_bookmark_missing_project_raises():
    with pytest.raises(BookmarkError, match="not found"):
        add_bookmark("ghost", "dev")


def test_remove_bookmark_clears_flag():
    add_bookmark("myproject", "dev")
    remove_bookmark("myproject", "dev")
    assert is_bookmarked("myproject", "dev") is False


def test_remove_bookmark_clears_label():
    add_bookmark("myproject", "dev", label="test label")
    remove_bookmark("myproject", "dev")
    assert get_bookmark_label("myproject", "dev") is None


def test_remove_non_bookmarked_raises():
    with pytest.raises(BookmarkError, match="not bookmarked"):
        remove_bookmark("myproject", "dev")


def test_is_bookmarked_false_by_default():
    assert is_bookmarked("myproject", "dev") is False


def test_list_bookmarks_empty():
    assert list_bookmarks() == []


def test_list_bookmarks_returns_all():
    add_bookmark("myproject", "dev", label="dev")
    add_bookmark("myproject", "prod")
    results = list_bookmarks()
    assert len(results) == 2
    projects = {r["project"] for r in results}
    profiles = {r["profile"] for r in results}
    assert projects == {"myproject"}
    assert profiles == {"dev", "prod"}


def test_list_bookmarks_includes_label():
    add_bookmark("myproject", "dev", label="my label")
    results = list_bookmarks()
    dev_entry = next(r for r in results if r["profile"] == "dev")
    assert dev_entry["label"] == "my label"


def test_list_bookmarks_label_none_when_not_set():
    add_bookmark("myproject", "prod")
    results = list_bookmarks()
    prod_entry = next(r for r in results if r["profile"] == "prod")
    assert prod_entry["label"] is None

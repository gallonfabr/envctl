"""Tests for envctl.tags module."""

import pytest
from unittest.mock import patch

from envctl import tags as tags_mod
from envctl.storage import load_profiles, save_profiles


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store = tmp_path / "store.json"
    monkeypatch.setattr("envctl.storage.get_store_path", lambda: store)
    # Seed a base profile
    data = {"myapp": {"dev": {"vars": {"FOO": "bar"}, "tags": []}}}
    save_profiles(data)
    yield


def test_add_tag():
    tags_mod.add_tag("myapp", "dev", "production")
    assert "production" in tags_mod.list_tags("myapp", "dev")


def test_add_tag_no_duplicate():
    tags_mod.add_tag("myapp", "dev", "staging")
    tags_mod.add_tag("myapp", "dev", "staging")
    assert tags_mod.list_tags("myapp", "dev").count("staging") == 1


def test_remove_tag():
    tags_mod.add_tag("myapp", "dev", "ci")
    tags_mod.remove_tag("myapp", "dev", "ci")
    assert "ci" not in tags_mod.list_tags("myapp", "dev")


def test_remove_missing_tag_raises():
    with pytest.raises(ValueError, match="not found"):
        tags_mod.remove_tag("myapp", "dev", "nonexistent")


def test_add_tag_missing_profile_raises():
    with pytest.raises(KeyError):
        tags_mod.add_tag("myapp", "ghost", "x")


def test_list_tags_empty():
    assert tags_mod.list_tags("myapp", "dev") == []


def test_find_by_tag():
    data = load_profiles()
    data["myapp"]["prod"] = {"vars": {}, "tags": ["live"]}
    data["myapp"]["dev"]["tags"] = ["live", "debug"]
    save_profiles(data)
    results = tags_mod.find_by_tag("live")
    assert ("myapp", "prod") in results
    assert ("myapp", "dev") in results


def test_find_by_tag_no_match():
    assert tags_mod.find_by_tag("nope") == []

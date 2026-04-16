"""Tests for the envctl storage module."""

import json
import os
import pytest
from pathlib import Path

from envctl.storage import (
    delete_profile,
    get_profile,
    list_profiles,
    list_projects,
    load_profiles,
    save_profile,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    """Redirect storage to a temporary directory for each test."""
    monkeypatch.setenv("ENVCTL_STORE_DIR", str(tmp_path))
    yield tmp_path


def test_load_profiles_empty():
    assert load_profiles() == {}


def test_save_and_get_profile():
    save_profile("myapp", "dev", {"DEBUG": "true", "PORT": "8000"})
    result = get_profile("myapp", "dev")
    assert result == {"DEBUG": "true", "PORT": "8000"}


def test_list_projects():
    save_profile("alpha", "staging", {"ENV": "staging"})
    save_profile("beta", "prod", {"ENV": "prod"})
    projects = list_projects()
    assert "alpha" in projects
    assert "beta" in projects


def test_list_profiles():
    save_profile("myapp", "dev", {"A": "1"})
    save_profile("myapp", "prod", {"A": "2"})
    profiles = list_profiles("myapp")
    assert set(profiles) == {"dev", "prod"}


def test_list_profiles_unknown_project():
    assert list_profiles("nonexistent") == []


def test_get_profile_missing():
    assert get_profile("ghost", "dev") is None


def test_delete_profile():
    save_profile("myapp", "dev", {"X": "1"})
    assert delete_profile("myapp", "dev") is True
    assert get_profile("myapp", "dev") is None


def test_delete_profile_removes_empty_project():
    save_profile("myapp", "dev", {"X": "1"})
    delete_profile("myapp", "dev")
    assert "myapp" not in list_projects()


def test_delete_profile_not_found():
    assert delete_profile("ghost", "dev") is False


def test_overwrite_profile():
    save_profile("myapp", "dev", {"KEY": "old"})
    save_profile("myapp", "dev", {"KEY": "new"})
    assert get_profile("myapp", "dev") == {"KEY": "new"}


def test_save_profile_empty_vars():
    """Saving a profile with an empty dict should persist and be retrievable."""
    save_profile("myapp", "empty", {})
    assert get_profile("myapp", "empty") == {}
    assert "empty" in list_profiles("myapp")


def test_delete_one_profile_keeps_others():
    """Deleting one profile should not affect sibling profiles in the same project."""
    save_profile("myapp", "dev", {"A": "1"})
    save_profile("myapp", "prod", {"A": "2"})
    delete_profile("myapp", "dev")
    assert get_profile("myapp", "prod") == {"A": "2"}
    assert "myapp" in list_projects()

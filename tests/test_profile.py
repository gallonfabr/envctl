"""Tests for envctl.profile management functions."""

import pytest
from unittest.mock import patch, MagicMock

from envctl import profile as prof


BASE_PROFILES: dict = {}


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    """Redirect storage to a temp file for each test."""
    store = tmp_path / "profiles.json"
    monkeypatch.setattr("envctl.storage.get_store_path", lambda: store)
    yield


def test_add_and_get_plain_profile():
    prof.add_profile("myapp", "dev", {"HOST": "localhost", "PORT": "5432"})
    vars_dict = prof.get_profile("myapp", "dev")
    assert vars_dict == {"HOST": "localhost", "PORT": "5432"}


def test_add_and_get_encrypted_profile():
    prof.add_profile("myapp", "prod", {"SECRET": "topsecret"}, password="pass")
    vars_dict = prof.get_profile("myapp", "prod", password="pass")
    assert vars_dict == {"SECRET": "topsecret"}


def test_get_encrypted_profile_without_password():
    prof.add_profile("myapp", "prod", {"SECRET": "x"}, password="pass")
    with pytest.raises(ValueError, match="Password required"):
        prof.get_profile("myapp", "prod")


def test_get_missing_profile():
    with pytest.raises(KeyError):
        prof.get_profile("ghost", "dev")


def test_delete_profile():
    prof.add_profile("myapp", "dev", {"A": "1"})
    prof.delete_profile("myapp", "dev")
    with pytest.raises(KeyError):
        prof.get_profile("myapp", "dev")


def test_delete_removes_empty_project():
    from envctl import storage
    prof.add_profile("solo", "only", {"X": "1"})
    prof.delete_profile("solo", "only")
    assert "solo" not in storage.list_projects()


def test_delete_missing_profile_raises():
    with pytest.raises(KeyError):
        prof.delete_profile("noproject", "noprofile")


def test_apply_profile_returns_strings():
    prof.add_profile("app", "ci", {"WORKERS": 4, "DEBUG": False})
    result = prof.apply_profile("app", "ci")
    assert result == {"WORKERS": "4", "DEBUG": "False"}

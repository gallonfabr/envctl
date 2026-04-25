"""Tests for envctl.label."""
import pytest

from envctl.label import (
    LabelError,
    clear_labels,
    find_by_label,
    get_labels,
    remove_label,
    set_label,
)
from envctl.storage import load_profiles, save_profiles


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    import envctl.storage as st
    monkeypatch.setattr(st, "get_store_path", lambda: tmp_path / "store.json")
    # seed two profiles
    save_profiles("proj", {"dev": {"vars": {}}, "prod": {"vars": {}}})


def test_set_label_persists():
    set_label("proj", "dev", "env", "development")
    labels = get_labels("proj", "dev")
    assert labels["env"] == "development"


def test_set_label_overwrites():
    set_label("proj", "dev", "tier", "free")
    set_label("proj", "dev", "tier", "paid")
    assert get_labels("proj", "dev")["tier"] == "paid"


def test_set_label_invalid_key_raises():
    with pytest.raises(LabelError, match="Invalid label key"):
        set_label("proj", "dev", "bad-key!", "val")


def test_set_label_missing_profile_raises():
    with pytest.raises(LabelError, match="not found"):
        set_label("proj", "ghost", "k", "v")


def test_remove_label_success():
    set_label("proj", "dev", "region", "us-east")
    remove_label("proj", "dev", "region")
    assert "region" not in get_labels("proj", "dev")


def test_remove_label_missing_key_raises():
    with pytest.raises(LabelError, match="not found"):
        remove_label("proj", "dev", "nonexistent")


def test_get_labels_empty():
    assert get_labels("proj", "dev") == {}


def test_get_labels_missing_profile_raises():
    with pytest.raises(LabelError, match="not found"):
        get_labels("proj", "missing")


def test_find_by_label_key_only():
    set_label("proj", "dev", "env", "development")
    set_label("proj", "prod", "env", "production")
    result = find_by_label("proj", "env")
    assert "dev" in result
    assert "prod" in result


def test_find_by_label_key_and_value():
    set_label("proj", "dev", "env", "development")
    set_label("proj", "prod", "env", "production")
    result = find_by_label("proj", "env", "development")
    assert result == ["dev"]


def test_find_by_label_no_matches():
    result = find_by_label("proj", "nonexistent")
    assert result == []


def test_clear_labels():
    set_label("proj", "dev", "a", "1")
    set_label("proj", "dev", "b", "2")
    clear_labels("proj", "dev")
    assert get_labels("proj", "dev") == {}


def test_clear_labels_missing_profile_raises():
    with pytest.raises(LabelError, match="not found"):
        clear_labels("proj", "ghost")

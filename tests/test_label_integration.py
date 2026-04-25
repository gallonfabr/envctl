"""Integration tests for label lifecycle."""
import pytest

from envctl.label import (
    LabelError,
    clear_labels,
    find_by_label,
    get_labels,
    remove_label,
    set_label,
)
from envctl.storage import save_profiles


@pytest.fixture()
def isolated(tmp_path, monkeypatch):
    import envctl.storage as st
    monkeypatch.setattr(st, "get_store_path", lambda: tmp_path / "store.json")
    save_profiles("app", {
        "alpha": {"vars": {}},
        "beta": {"vars": {}},
        "gamma": {"vars": {}},
    })


def test_full_label_lifecycle(isolated):
    set_label("app", "alpha", "tier", "free")
    set_label("app", "beta", "tier", "pro")
    set_label("app", "gamma", "tier", "free")

    assert find_by_label("app", "tier", "free") == ["alpha", "gamma"]
    assert find_by_label("app", "tier", "pro") == ["beta"]

    set_label("app", "alpha", "tier", "pro")
    assert find_by_label("app", "tier", "free") == ["gamma"]

    remove_label("app", "gamma", "tier")
    assert find_by_label("app", "tier") == ["alpha", "beta"]


def test_multiple_labels_on_profile(isolated):
    set_label("app", "alpha", "owner", "alice")
    set_label("app", "alpha", "region", "us-west")
    set_label("app", "alpha", "tier", "free")
    labels = get_labels("app", "alpha")
    assert len(labels) == 3
    assert labels["owner"] == "alice"
    assert labels["region"] == "us-west"


def test_clear_then_re_add(isolated):
    set_label("app", "beta", "x", "old")
    clear_labels("app", "beta")
    assert get_labels("app", "beta") == {}
    set_label("app", "beta", "x", "new")
    assert get_labels("app", "beta")["x"] == "new"


def test_labels_independent_across_profiles(isolated):
    set_label("app", "alpha", "key", "val")
    assert "key" not in get_labels("app", "beta")

"""Tests for envctl.snapshot module."""

import pytest
from unittest.mock import patch
from envctl import snapshot as snap
from envctl.snapshot import (
    create_snapshot,
    list_snapshots,
    restore_snapshot,
    delete_snapshot,
    SNAPSHOT_PROJECT,
)


@pytest.fixture(autouse=True)
def reset_profiles(tmp_path, monkeypatch):
    store = tmp_path / "profiles.json"
    monkeypatch.setattr("envctl.storage.get_store_path", lambda: store)
    yield


def _seed(project, profile, vars_):
    from envctl.storage import load_profiles, save_profiles
    p = load_profiles()
    p.setdefault(project, {})[profile] = {"encrypted": False, "vars": vars_}
    save_profiles(p)


def test_create_snapshot_returns_key():
    _seed("myapp", "dev", {"FOO": "bar"})
    key = create_snapshot("myapp", "dev")
    assert key.startswith("myapp__dev__")


def test_create_snapshot_stores_data():
    _seed("myapp", "dev", {"FOO": "bar"})
    key = create_snapshot("myapp", "dev")
    snaps = list_snapshots()
    keys = [s["key"] for s in snaps]
    assert key in keys


def test_create_snapshot_missing_profile():
    with pytest.raises(KeyError, match="Profile 'dev' not found"):
        create_snapshot("ghost", "dev")


def test_list_snapshots_filter_by_project():
    _seed("app1", "prod", {"A": "1"})
    _seed("app2", "prod", {"B": "2"})
    create_snapshot("app1", "prod")
    create_snapshot("app2", "prod")
    snaps = list_snapshots(project="app1")
    assert all(s["project"] == "app1" for s in snaps)
    assert len(snaps) == 1


def test_list_snapshots_empty():
    """list_snapshots returns an empty list when no snapshots exist."""
    snaps = list_snapshots()
    assert snaps == []


def test_list_snapshots_filter_no_match():
    """list_snapshots returns empty list when project filter matches nothing."""
    _seed("myapp", "dev", {"FOO": "bar"})
    create_snapshot("myapp", "dev")
    snaps = list_snapshots(project="nonexistent")
    assert snaps == []


def test_restore_snapshot():
    _seed("myapp", "dev", {"FOO": "original"})
    key = create_snapshot("myapp", "dev")
    # mutate original
    _seed("myapp", "dev", {"FOO": "changed"})
    restore_snapshot(key, "myapp", "restored")
    from envctl.storage import load_profiles
    p = load_profiles()
    assert p["myapp"]["restored"]["vars"]["FOO"] == "original"


def test_restore_snapshot_missing():
    with pytest.raises(KeyError, match="Snapshot 'bad_key' not found"):
        restore_snapshot("bad_key", "myapp", "dev")


def test_delete_snapshot():
    _seed("myapp", "dev", {"X": "y"})
    key = create_snapshot("myapp", "dev")
    delete_snapshot(key)
    snaps = list_snapshots()
    assert all(s["key"] != key for s in snaps)


def test_delete_snapshot_missing():
    with pytest.raises(KeyError, match="Snapshot 'nope' not found"):
        delete_snapshot("nope")

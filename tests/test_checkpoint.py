"""Tests for envctl.checkpoint module."""
import pytest
from unittest.mock import patch, MagicMock

from envctl.checkpoint import (
    CheckpointError,
    create_checkpoint,
    restore_checkpoint,
    list_checkpoints,
    delete_checkpoint,
)


BASE_DATA = {
    "projects": {
        "myapp": {
            "dev": {"vars": {"DB_HOST": "localhost", "PORT": "5432"}}
        }
    }
}


def _copy(d):
    import copy
    return copy.deepcopy(d)


@pytest.fixture()
def patch_deps():
    store = _copy(BASE_DATA)
    with (
        patch("envctl.checkpoint.load_profiles", return_value=store) as lp,
        patch("envctl.checkpoint.save_profiles") as sp,
        patch("envctl.checkpoint.log_event") as le,
    ):
        lp.side_effect = lambda: _copy(store)
        sp.side_effect = lambda d: store.update(d)
        yield lp, sp, le, store


def test_create_checkpoint_returns_entry(patch_deps):
    lp, sp, le, store = patch_deps
    entry = create_checkpoint("myapp", "dev", "v1")
    assert "vars" in entry
    assert entry["vars"] == {"DB_HOST": "localhost", "PORT": "5432"}
    assert "created_at" in entry


def test_create_checkpoint_persists(patch_deps):
    lp, sp, le, store = patch_deps
    create_checkpoint("myapp", "dev", "v1")
    sp.assert_called_once()
    saved = sp.call_args[0][0]
    cps = saved["projects"]["myapp"]["dev"]["_meta"]["checkpoints"]
    assert "v1" in cps


def test_create_checkpoint_logs_event(patch_deps):
    lp, sp, le, store = patch_deps
    create_checkpoint("myapp", "dev", "v1")
    le.assert_called_once_with("myapp", "dev", "checkpoint_created", {"name": "v1"})


def test_create_checkpoint_missing_profile_raises(patch_deps):
    with pytest.raises(CheckpointError, match="not found"):
        create_checkpoint("myapp", "prod", "v1")


def test_create_checkpoint_empty_name_raises(patch_deps):
    with pytest.raises(CheckpointError, match="empty"):
        create_checkpoint("myapp", "dev", "  ")


def test_restore_checkpoint_updates_vars(patch_deps):
    lp, sp, le, store = patch_deps
    create_checkpoint("myapp", "dev", "snap")
    restore_checkpoint("myapp", "dev", "snap")
    le.assert_called_with("myapp", "dev", "checkpoint_restored", {"name": "snap"})


def test_restore_checkpoint_missing_raises(patch_deps):
    with pytest.raises(CheckpointError, match="not found"):
        restore_checkpoint("myapp", "dev", "nonexistent")


def test_list_checkpoints_empty(patch_deps):
    result = list_checkpoints("myapp", "dev")
    assert result == []


def test_list_checkpoints_sorted_newest_first(patch_deps):
    lp, sp, le, store = patch_deps
    import time
    create_checkpoint("myapp", "dev", "old")
    time.sleep(0.01)
    create_checkpoint("myapp", "dev", "new")
    items = list_checkpoints("myapp", "dev")
    assert items[0]["name"] == "new"
    assert items[1]["name"] == "old"


def test_delete_checkpoint_removes_entry(patch_deps):
    lp, sp, le, store = patch_deps
    create_checkpoint("myapp", "dev", "v1")
    delete_checkpoint("myapp", "dev", "v1")
    items = list_checkpoints("myapp", "dev")
    assert all(i["name"] != "v1" for i in items)


def test_delete_checkpoint_missing_raises(patch_deps):
    with pytest.raises(CheckpointError, match="not found"):
        delete_checkpoint("myapp", "dev", "ghost")

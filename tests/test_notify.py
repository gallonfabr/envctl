"""Tests for envctl.notify."""
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import envctl.notify as notify


@pytest.fixture(autouse=True)
def isolated_hooks(tmp_path, monkeypatch):
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    store_file = store_dir / "profiles.json"
    store_file.write_text("{}")
    monkeypatch.setattr(notify, "_get_hooks_path", lambda: tmp_path / "hooks.json")
    yield tmp_path


def test_list_hooks_empty():
    assert notify.list_hooks() == {}


def test_set_and_get_hook():
    notify.set_hook("apply", "echo applied")
    assert notify.get_hook("apply") == "echo applied"


def test_set_hook_overwrites():
    notify.set_hook("apply", "echo first")
    notify.set_hook("apply", "echo second")
    assert notify.get_hook("apply") == "echo second"


def test_remove_hook():
    notify.set_hook("delete", "echo deleted")
    notify.remove_hook("delete")
    assert notify.get_hook("delete") is None


def test_remove_missing_hook_no_error():
    notify.remove_hook("nonexistent")  # should not raise


def test_list_hooks_returns_all():
    notify.set_hook("apply", "echo apply")
    notify.set_hook("add", "echo add")
    hooks = notify.list_hooks()
    assert hooks == {"apply": "echo apply", "add": "echo add"}


def test_fire_no_hook_returns_none():
    result = notify.fire("unknown_event")
    assert result is None


def test_fire_runs_command():
    notify.set_hook("apply", "exit 0")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        code = notify.fire("apply")
    assert code == 0
    mock_run.assert_called_once()


def test_fire_passes_env_vars():
    notify.set_hook("apply", "printenv ENVCTL_PROJECT")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        notify.fire("apply", env_vars={"ENVCTL_PROJECT": "myapp"})
    _, kwargs = mock_run.call_args
    assert kwargs["env"]["ENVCTL_PROJECT"] == "myapp"


def test_fire_returns_exit_code():
    notify.set_hook("delete", "exit 1")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        code = notify.fire("delete")
    assert code == 1

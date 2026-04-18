"""Tests for envctl.inherit."""
import pytest
from unittest.mock import patch, call

from envctl.inherit import inherit_profile, InheritError

PARENT_VARS = {"HOST": "localhost", "PORT": "5432", "DEBUG": "false"}
CHILD_VARS = {"DEBUG": "true", "SECRET": "abc"}


@pytest.fixture()
def patch_deps():
    with patch("envctl.inherit.get_profile") as mock_get, \
         patch("envctl.inherit.add_profile") as mock_add, \
         patch("envctl.inherit.log_event") as mock_log:
        yield mock_get, mock_add, mock_log


def test_inherit_no_existing_child(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    mock_get.side_effect = [PARENT_VARS, None]

    result = inherit_profile("app", "dev", "base", "default")

    assert result == PARENT_VARS
    mock_add.assert_called_once_with("app", "dev", PARENT_VARS, password=None, overwrite=True)


def test_inherit_child_overrides_parent(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    mock_get.side_effect = [PARENT_VARS, CHILD_VARS]

    result = inherit_profile("app", "dev", "base", "default")

    assert result["DEBUG"] == "true"       # child wins
    assert result["HOST"] == "localhost"   # parent default
    assert result["SECRET"] == "abc"       # child-only key


def test_inherit_missing_parent_raises(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    mock_get.return_value = None

    with pytest.raises(InheritError, match="Parent profile"):
        inherit_profile("app", "dev", "base", "missing")


def test_inherit_logs_event(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    mock_get.side_effect = [PARENT_VARS, None]

    inherit_profile("app", "dev", "base", "default")

    mock_log.assert_called_once_with(
        "app", "dev", "inherit", detail="parent=base/default"
    )


def test_inherit_passes_passwords(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    mock_get.side_effect = [PARENT_VARS, CHILD_VARS]

    inherit_profile(
        "app", "dev", "base", "default",
        password="childpw",
        parent_password="parentpw",
    )

    calls = mock_get.call_args_list
    assert calls[0] == call("base", "default", password="parentpw")
    assert calls[1] == call("app", "dev", password="childpw")
    mock_add.assert_called_once()
    _, kwargs = mock_add.call_args
    assert kwargs["password"] == "childpw"

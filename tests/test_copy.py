"""Tests for envctl.copy module."""

import pytest
from unittest.mock import patch, call

from envctl.copy import copy_profile, rename_profile


SRC_VARS = {"KEY": "value", "FOO": "bar"}


def _mock_get(project, profile, password=None):
    if project == "proj" and profile == "dev":
        return dict(SRC_VARS)
    return None


@pytest.fixture(autouse=True)
def patch_deps():
    with patch("envctl.copy.get_profile", side_effect=_mock_get), \
         patch("envctl.copy.add_profile") as mock_add, \
         patch("envctl.copy.log_event") as mock_log:
        yield mock_add, mock_log


def test_copy_profile_calls_add(patch_deps):
    mock_add, _ = patch_deps
    copy_profile("proj", "dev", "proj2", "staging")
    mock_add.assert_called_once_with("proj2", "staging", SRC_VARS, password=None)


def test_copy_profile_logs_event(patch_deps):
    _, mock_log = patch_deps
    copy_profile("proj", "dev", "proj2", "staging")
    mock_log.assert_called_once()
    args = mock_log.call_args[0]
    assert args[0] == "proj2"
    assert args[1] == "copy"


def test_copy_profile_missing_src(patch_deps):
    with pytest.raises(ValueError, match="not found"):
        copy_profile("proj", "missing", "proj2", "staging")


def test_copy_profile_with_password(patch_deps):
    mock_add, _ = patch_deps
    copy_profile("proj", "dev", "proj", "dev-copy", password="secret")
    mock_add.assert_called_once_with("proj", "dev-copy", SRC_VARS, password="secret")


def test_rename_profile_adds_and_deletes(patch_deps):
    mock_add, _ = patch_deps
    with patch("envctl.copy.delete_profile") as mock_del:
        rename_profile("proj", "dev", "development")
        mock_add.assert_called_once_with("proj", "development", SRC_VARS, password=None)
        mock_del.assert_called_once_with("proj", "dev")


def test_rename_profile_logs_event(patch_deps):
    _, mock_log = patch_deps
    with patch("envctl.copy.delete_profile"):
        rename_profile("proj", "dev", "development")
    mock_log.assert_called_once()
    args = mock_log.call_args[0]
    assert args[1] == "rename"


def test_rename_profile_missing_src(patch_deps):
    with pytest.raises(ValueError, match="not found"):
        rename_profile("proj", "ghost", "new-name")

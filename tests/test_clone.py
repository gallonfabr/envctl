"""Tests for envctl.clone."""
import pytest
from unittest.mock import patch, MagicMock
from envctl.clone import clone_profile, mirror_project


@pytest.fixture
def patch_deps():
    with patch("envctl.clone.get_profile") as mock_get, \
         patch("envctl.clone.add_profile") as mock_add, \
         patch("envctl.clone.log_event") as mock_log:
        yield mock_get, mock_add, mock_log


def test_clone_profile_success(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    mock_get.return_value = {"KEY": "val"}
    result = clone_profile("proj_a", "dev", "proj_b", "dev")
    assert result == {"KEY": "val"}
    mock_add.assert_called_once_with("proj_b", "dev", {"KEY": "val"}, password=None)
    mock_log.assert_called_once()


def test_clone_profile_with_password(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    mock_get.return_value = {"SECRET": "x"}
    clone_profile("proj_a", "prod", "proj_b", "prod", password="pw")
    mock_get.assert_called_once_with("proj_a", "prod", password="pw")
    mock_add.assert_called_once_with("proj_b", "prod", {"SECRET": "x"}, password="pw")


def test_clone_profile_missing_src(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    mock_get.return_value = None
    with pytest.raises(KeyError, match="dev"):
        clone_profile("proj_a", "dev", "proj_b", "dev")
    mock_add.assert_not_called()


def test_clone_logs_event(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    mock_get.return_value = {"A": "1"}
    clone_profile("src", "p", "dst", "q")
    args = mock_log.call_args
    assert args[0][0] == "clone"
    assert args[1]["meta"]["src_project"] == "src"


def test_mirror_project(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    mock_get.return_value = {"K": "v"}
    result = mirror_project("src", "dst", ["dev", "prod"])
    assert result == ["dev", "prod"]
    assert mock_add.call_count == 2


def test_mirror_project_empty(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    result = mirror_project("src", "dst", [])
    assert result == []
    mock_add.assert_not_called()

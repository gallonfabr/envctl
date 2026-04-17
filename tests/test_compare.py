"""Tests for envctl.compare module."""
import pytest
from unittest.mock import patch, MagicMock
from envctl.compare import compare_profiles, compare_summary


PROFILE_A = {"DB_HOST": "localhost", "DB_PORT": "5432", "DEBUG": "true"}
PROFILE_B = {"DB_HOST": "prod.db", "DB_PORT": "5432", "LOG_LEVEL": "warn"}


@pytest.fixture()
def patch_deps():
    with patch("envctl.compare.get_profile") as mock_get, \
         patch("envctl.compare.log_event") as mock_log:
        yield mock_get, mock_log


def test_compare_added_keys(patch_deps):
    mock_get, _ = patch_deps
    mock_get.side_effect = [PROFILE_A, PROFILE_B]
    diff = compare_profiles("proj", "dev", "proj", "prod")
    assert "LOG_LEVEL" in diff["added"]


def test_compare_removed_keys(patch_deps):
    mock_get, _ = patch_deps
    mock_get.side_effect = [PROFILE_A, PROFILE_B]
    diff = compare_profiles("proj", "dev", "proj", "prod")
    assert "DEBUG" in diff["removed"]


def test_compare_changed_keys(patch_deps):
    mock_get, _ = patch_deps
    mock_get.side_effect = [PROFILE_A, PROFILE_B]
    diff = compare_profiles("proj", "dev", "proj", "prod")
    assert "DB_HOST" in diff["changed"]


def test_compare_logs_event(patch_deps):
    mock_get, mock_log = patch_deps
    mock_get.side_effect = [PROFILE_A, PROFILE_B]
    compare_profiles("proj", "dev", "proj", "prod")
    mock_log.assert_called_once()
    args = mock_log.call_args[0]
    assert args[0] == "proj"
    assert args[1] == "compare"


def test_compare_identical_profiles(patch_deps):
    mock_get, _ = patch_deps
    mock_get.side_effect = [PROFILE_A, PROFILE_A.copy()]
    diff = compare_profiles("proj", "dev", "proj", "dev2")
    assert diff["added"] == {}
    assert diff["removed"] == {}
    assert diff["changed"] == {}


def test_compare_summary_counts():
    diff = {
        "added": {"A": "1"},
        "removed": {"B": "2", "C": "3"},
        "changed": {},
    }
    summary = compare_summary(diff)
    assert "+1" in summary
    assert "-2" in summary
    assert "~0" in summary


def test_compare_missing_profile_raises(patch_deps):
    mock_get, _ = patch_deps
    mock_get.side_effect = KeyError("Profile not found")
    with pytest.raises(KeyError):
        compare_profiles("proj", "missing", "proj", "prod")

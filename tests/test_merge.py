"""Tests for envctl.merge."""

import pytest
from unittest.mock import patch, call
from envctl.merge import merge_profiles, STRATEGY_OURS, STRATEGY_THEIRS, STRATEGY_ERROR


BASE_VARS = {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
OTHER_VARS = {"HOST": "remotehost", "PORT": "5432", "TIMEOUT": "30"}


@pytest.fixture()
def patch_deps():
    with patch("envctl.merge.get_profile") as mock_get, \
         patch("envctl.merge.add_profile") as mock_add, \
         patch("envctl.merge.log_event") as mock_log:
        mock_get.side_effect = lambda proj, name: (
            BASE_VARS if name == "base" else OTHER_VARS
        )
        yield mock_get, mock_add, mock_log


def test_merge_no_conflicts(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    result = merge_profiles("myapp", "base", "other", "merged", strategy=STRATEGY_OURS)
    assert result["TIMEOUT"] == "30"
    assert result["PORT"] == "5432"
    mock_add.assert_called_once()
    mock_log.assert_called_once()


def test_merge_strategy_ours_keeps_base(patch_deps):
    mock_get, mock_add, _ = patch_deps
    result = merge_profiles("myapp", "base", "other", "merged", strategy=STRATEGY_OURS)
    assert result["HOST"] == "localhost"


def test_merge_strategy_theirs_takes_other(patch_deps):
    mock_get, mock_add, _ = patch_deps
    result = merge_profiles("myapp", "base", "other", "merged", strategy=STRATEGY_THEIRS)
    assert result["HOST"] == "remotehost"


def test_merge_strategy_error_raises_on_conflict(patch_deps):
    with pytest.raises(ValueError, match="Merge conflict on keys: HOST"):
        merge_profiles("myapp", "base", "other", "merged", strategy=STRATEGY_ERROR)


def test_merge_invalid_strategy(patch_deps):
    with pytest.raises(ValueError, match="Unknown strategy"):
        merge_profiles("myapp", "base", "other", "merged", strategy="invalid")


def test_merge_passes_password(patch_deps):
    mock_get, mock_add, _ = patch_deps
    merge_profiles("myapp", "base", "other", "merged", strategy=STRATEGY_OURS, password="s3cr3t")
    _, kwargs = mock_add.call_args
    assert kwargs.get("password") == "s3cr3t"


def test_merge_logs_correct_event(patch_deps):
    mock_get, mock_add, mock_log = patch_deps
    merge_profiles("myapp", "base", "other", "merged", strategy=STRATEGY_OURS)
    mock_log.assert_called_once_with(
        "myapp", "merged", "merge",
        {"base": "base", "other": "other", "strategy": STRATEGY_OURS},
    )

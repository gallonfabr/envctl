"""Tests for envctl.replay."""
from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from envctl.replay import ReplayError, ReplayResult, replay_project, replay_summary

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_HISTORY = [
    {"profile": "prod", "applied_at": "2024-06-01T12:00:00"},
    {"profile": "staging", "applied_at": "2024-06-01T11:00:00"},
    {"profile": "dev", "applied_at": "2024-06-01T10:00:00"},
]


@pytest.fixture()
def patch_deps():
    with patch("envctl.replay.get_history") as mock_hist, \
         patch("envctl.replay.apply_profile") as mock_apply, \
         patch("envctl.replay.log_event") as mock_log:
        mock_hist.return_value = _HISTORY
        yield mock_hist, mock_apply, mock_log


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_replay_single_step(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    result = replay_project("myapp", steps=1)
    assert result.replayed == ["prod"]
    assert result.skipped == []
    mock_apply.assert_called_once_with("myapp", "prod", password=None)


def test_replay_multiple_steps(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    result = replay_project("myapp", steps=3)
    # replayed in reversed (oldest-first) order
    assert result.replayed == ["dev", "staging", "prod"]
    assert mock_apply.call_count == 3


def test_replay_logs_event(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    replay_project("myapp", steps=1)
    mock_log.assert_called_once_with("myapp", "prod", "replay")


def test_replay_skips_missing_profile(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    mock_apply.side_effect = KeyError("prod")
    result = replay_project("myapp", steps=1)
    assert result.replayed == []
    assert result.skipped == ["prod"]
    mock_log.assert_not_called()


def test_replay_zero_steps_raises():
    with pytest.raises(ReplayError, match="steps must be >= 1"):
        replay_project("myapp", steps=0)


def test_replay_no_history_raises(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    mock_hist.return_value = []
    with pytest.raises(ReplayError, match="No apply history"):
        replay_project("myapp")


def test_replay_passes_password(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    replay_project("myapp", steps=1, password="secret")
    mock_apply.assert_called_once_with("myapp", "prod", password="secret")


def test_replay_summary_with_skipped():
    result = ReplayResult(project="myapp", replayed=["prod"], skipped=["ghost"])
    summary = replay_summary(result)
    assert "Replayed: prod" in summary
    assert "Skipped (missing): ghost" in summary


def test_replay_summary_nothing_replayed():
    result = ReplayResult(project="myapp", replayed=[], skipped=["ghost"])
    summary = replay_summary(result)
    assert "Nothing replayed" in summary

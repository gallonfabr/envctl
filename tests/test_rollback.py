"""Tests for envctl.rollback."""

import pytest
from unittest.mock import patch, MagicMock

from envctl.rollback import rollback, rollback_to, RollbackError

HISTORY = [
    {"profile": "prod", "applied_at": "2024-01-03T10:00:00"},
    {"profile": "staging", "applied_at": "2024-01-02T10:00:00"},
    {"profile": "dev", "applied_at": "2024-01-01T10:00:00"},
]


@pytest.fixture()
def patch_deps():
    with patch("envctl.rollback.get_history") as mock_hist, \
         patch("envctl.rollback.apply_profile") as mock_apply, \
         patch("envctl.rollback.log_event") as mock_log:
        mock_hist.return_value = HISTORY
        mock_apply.return_value = {"KEY": "val"}
        yield mock_hist, mock_apply, mock_log


def test_rollback_one_step(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    result = rollback("myapp", steps=1)
    mock_apply.assert_called_once_with("myapp", "staging", password=None)
    assert result["profile"] == "staging"


def test_rollback_two_steps(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    result = rollback("myapp", steps=2)
    mock_apply.assert_called_once_with("myapp", "dev", password=None)
    assert result["profile"] == "dev"


def test_rollback_logs_event(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    rollback("myapp", steps=1)
    mock_log.assert_called_once()
    call_kwargs = mock_log.call_args.kwargs
    assert call_kwargs["action"] == "rollback"
    assert call_kwargs["profile"] == "staging"


def test_rollback_not_enough_history(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    with pytest.raises(RollbackError, match="Not enough history"):
        rollback("myapp", steps=10)


def test_rollback_invalid_steps(patch_deps):
    with pytest.raises(RollbackError, match="steps must be >= 1"):
        rollback("myapp", steps=0)


def test_rollback_with_password(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    rollback("myapp", steps=1, password="secret")
    mock_apply.assert_called_once_with("myapp", "staging", password="secret")


def test_rollback_to_success(patch_deps):
    mock_hist, mock_apply, mock_log = patch_deps
    result = rollback_to("myapp", "dev")
    mock_apply.assert_called_once_with("myapp", "dev", password=None)
    assert result["profile"] == "dev"
    mock_log.assert_called_once()
    assert mock_log.call_args.kwargs["action"] == "rollback_to"


def test_rollback_to_not_in_history(patch_deps):
    with pytest.raises(RollbackError, match="not found in apply history"):
        rollback_to("myapp", "unknown-profile")

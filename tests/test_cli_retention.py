"""Tests for envctl.cli_retention."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envctl.cli_retention import retention_cmd
from envctl.retention import RetentionError


@pytest.fixture()
def runner():
    return CliRunner()


def test_set_retention_success(runner):
    with patch("envctl.cli_retention.set_retention") as mock_set:
        result = runner.invoke(retention_cmd, ["set", "myproject", "30"])
    assert result.exit_code == 0
    assert "30 day(s)" in result.output
    mock_set.assert_called_once_with("myproject", 30)


def test_set_retention_error(runner):
    with patch("envctl.cli_retention.set_retention", side_effect=RetentionError("bad")):
        result = runner.invoke(retention_cmd, ["set", "myproject", "0"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_show_retention_set(runner):
    with patch("envctl.cli_retention.get_retention", return_value=14):
        result = runner.invoke(retention_cmd, ["show", "myproject"])
    assert result.exit_code == 0
    assert "14 day(s)" in result.output


def test_show_retention_not_set(runner):
    with patch("envctl.cli_retention.get_retention", return_value=None):
        result = runner.invoke(retention_cmd, ["show", "myproject"])
    assert result.exit_code == 0
    assert "No retention policy" in result.output


def test_clear_retention_success(runner):
    with patch("envctl.cli_retention.clear_retention") as mock_clear:
        result = runner.invoke(retention_cmd, ["clear", "myproject"])
    assert result.exit_code == 0
    assert "cleared" in result.output
    mock_clear.assert_called_once_with("myproject")


def test_apply_retention_purges(runner):
    with patch("envctl.cli_retention.apply_retention", return_value=["dev", "staging"]):
        result = runner.invoke(retention_cmd, ["apply", "myproject"])
    assert result.exit_code == 0
    assert "Purged: dev" in result.output
    assert "Purged: staging" in result.output


def test_apply_retention_dry_run(runner):
    with patch("envctl.cli_retention.apply_retention", return_value=["old"]) as mock_apply:
        result = runner.invoke(retention_cmd, ["apply", "myproject", "--dry-run"])
    assert result.exit_code == 0
    assert "Would purge: old" in result.output
    mock_apply.assert_called_once_with("myproject", dry_run=True)


def test_apply_retention_nothing_to_purge(runner):
    with patch("envctl.cli_retention.apply_retention", return_value=[]):
        result = runner.invoke(retention_cmd, ["apply", "myproject"])
    assert result.exit_code == 0
    assert "No profiles eligible" in result.output


def test_apply_retention_no_policy_error(runner):
    with patch("envctl.cli_retention.apply_retention", side_effect=RetentionError("No retention policy")):
        result = runner.invoke(retention_cmd, ["apply", "myproject"])
    assert result.exit_code == 1
    assert "Error" in result.output

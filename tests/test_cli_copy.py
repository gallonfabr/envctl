"""Tests for CLI copy/rename commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from envctl.cli_copy import copy_cmd


@pytest.fixture
def runner():
    return CliRunner()


def test_copy_profile_success(runner):
    with patch("envctl.cli_copy.copy_profile") as mock_copy:
        result = runner.invoke(
            copy_cmd, ["profile", "proj", "dev", "proj2", "staging"]
        )
        assert result.exit_code == 0
        assert "Copied" in result.output
        mock_copy.assert_called_once_with("proj", "dev", "proj2", "staging", password=None)


def test_copy_profile_with_password(runner):
    with patch("envctl.cli_copy.copy_profile") as mock_copy:
        result = runner.invoke(
            copy_cmd, ["profile", "proj", "dev", "proj2", "staging", "-p", "secret"]
        )
        assert result.exit_code == 0
        mock_copy.assert_called_once_with("proj", "dev", "proj2", "staging", password="secret")


def test_copy_profile_missing_src(runner):
    with patch("envctl.cli_copy.copy_profile", side_effect=ValueError("not found")):
        result = runner.invoke(
            copy_cmd, ["profile", "proj", "ghost", "proj2", "staging"]
        )
        assert result.exit_code == 1
        assert "Error" in result.output


def test_rename_profile_success(runner):
    with patch("envctl.cli_copy.rename_profile") as mock_rename:
        result = runner.invoke(copy_cmd, ["rename", "proj", "dev", "development"])
        assert result.exit_code == 0
        assert "Renamed" in result.output
        mock_rename.assert_called_once_with("proj", "dev", "development", password=None)


def test_rename_profile_missing(runner):
    with patch("envctl.cli_copy.rename_profile", side_effect=ValueError("not found")):
        result = runner.invoke(copy_cmd, ["rename", "proj", "ghost", "new"])
        assert result.exit_code == 1
        assert "Error" in result.output
